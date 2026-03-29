import json
import logging
import base64
from typing import Any, List, Dict, Optional, Literal
from pydantic import BaseModel, ValidationError, model_validator

log = logging.getLogger(__name__)


class InteractiveElement(BaseModel):
    id: int
    tag: str
    text: str
    role: str


class Action(BaseModel):
    action: str
    # Use -1 instead of None. Vertex AI ONLY wants a pure 'integer' type.
    selected_id: int = -1
    text_to_type: str = ""
    done: bool

    @model_validator(mode="after")
    def check_fields(self) -> "Action":
        targeting = ("click", "type", "scroll", "hover", "enter", "clear")
        if self.action in targeting:
            # Check for our sentinel -1 instead of None
            if self.selected_id == -1:
                raise ValueError(f"'selected_id' is required for '{self.action}'.")
        return self


class DOMActionAgent:
    def __init__(
            self,
            model_name: str = "gemini-2.5-flash",
            temperature: float = 0.4,
            max_output_tokens: int = 65500,
    ) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self._model = None
        self._response_schema = Action.model_json_schema()
        # Put the prompt inside the class so it's never lost
        self.system_prompt = """You are DOMActionAgent, a strategic browser controller for accessibility.
        You receive a USER INTENT (which includes the PREVIOUS STEP taken) and the current DOM state.

        ### STRATEGY RULES
        1. MEMORY AWARENESS: Look at the 'PREVIOUS STEP' in the intent. 
           - If you just 'type' text and the textbox is now filled, DO NOT type again. 
           - Instead, use 'enter' on that ID or 'click' the search/submit button.
        2. SEARCH LOGIC: A 'search' intent is only 'done: true' when results are visible. 
           - Sequence: type -> enter (or click search button) -> wait/verify.
        3. EMAILING: For 'write email' intents, generate high-quality, professional body text.
        4. NAVIGATION: If the intent is to 'Open [X]' and you click a link to [X], you may set 'done: true'.

        ### ACTION TYPES
        - "click"  (selected_id): For buttons and links.
        - "type"   (selected_id, text_to_type): For input. (Set done: false if you need to submit next).
        - "enter"  (selected_id): Press Enter on an element (Best for submitting searches).
        - "scroll" (selected_id): Bring element into view.
        - "hover"  (selected_id): Reveal hidden menus.
        - "clear"  (selected_id): Wipe existing text.
        - "wait": Use if the page is still loading.
        - "back": Go to previous page.

        ### CONSTRAINTS
        - Return exactly ONE action.
        - selected_id MUST be a raw integer (no floats like 1.0).
        - reasoning: Provide a 1-sentence explanation of why this step is next.
        - Set 'done: true' ONLY when the final goal is reached or the final submission is fired."""

    @property
    def model(self):
        if self._model is None:
            from vertexai.generative_models import GenerativeModel
            self._model = GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_prompt,
            )
        return self._model

    def __call__(
            self,
            corrected_text: str,
            elements: List[Dict[str, Any]],
            current_url: str = "",
    ) -> Optional[Dict[str, Any]]:
        return self.next_action(corrected_text, elements, current_url)

    def next_action(
            self,
            corrected_text: str,
            elements: List[Dict[str, Any]],
            current_url: str = "",
    ) -> Optional[Dict[str, Any]]:
        import traceback # Added for debugging
        from vertexai.generative_models import GenerationConfig

        intent = (corrected_text or "").strip()
        if not intent or not elements:
            print("DEBUG: Missing intent or elements, returning None", flush=True)
            return None

        try:
            # 1. Validate inputs
            validated_elements = [InteractiveElement.model_validate(e) for e in elements]

            # 2. Setup Generation Config
            gen_config = GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                response_mime_type="application/json",
                response_schema=self._response_schema,
            )

            # 3. Call Gemini
            print(f"DEBUG: Calling Planner for intent: {intent}", flush=True)
            response = self.model.generate_content(
                self._build_prompt(intent, validated_elements, current_url),
                generation_config=gen_config,
            )

            full_response_text = response.text.strip()
            print(f"DEBUG: Raw Planner Output: \n{full_response_text}\n", flush=True)

            # Find the JSON block
            start_idx = full_response_text.find('{')
            end_idx = full_response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError(f"No JSON block found in response: {full_response_text}")

            clean_json_str = full_response_text[start_idx:end_idx]

            parsed_data = json.loads(clean_json_str)
            validated_action = Action.model_validate(parsed_data)

            result = validated_action.model_dump()
            print(f"DEBUG: Validated Action: {result}", flush=True)
            return result

        except Exception as e:
            error_detail = traceback.format_exc()
            log.error(f"Cloud Agent Error: {error_detail}")
            # Returning error info so your Mac terminal shows the problem
            return {
                "error": str(e),
                "done": True,
                "debug_info": error_detail[:200]
            }

    def _build_prompt(self, intent, elements, url):
        return f"USER INTENT: {intent}\nURL: {url}\nELEMENTS: {json.dumps([e.model_dump() for e in elements])}"

