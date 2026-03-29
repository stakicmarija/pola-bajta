import json
import logging
import traceback  # Added for detailed error reporting
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class TremorFilterResponse(BaseModel):
    corrected_text: str = Field(..., description="The cleaned sentence.")


class TremorFilterAgent:
    def __init__(
            self,
            model_name: str = "gemini-2.5-flash",
            temperature: float = 0.4,
            max_output_tokens: int = 1024,
    ) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self._model = None

        self.system_prompt = """
        CONTEXT:
        You are the core Denoising Engine for an assistive technology suite. The user has a physical tremor.

        YOUR MISSION:
        Transform "noisy" keyboard input into the single most likely intended command or sentence. 

        RULES:
        1. DE-DUPLICATION: Remove repeated characters.
        2. OUTPUT FORMAT: Return ONLY a valid JSON object with key "corrected_text".

        EXAMPLES:
        - Input: "ooopppennn gmmaiiil"
          Output: {"corrected_text": "open gmail"}
        """.strip()

    @property
    def model(self):
        if self._model is None:
            # Using a more explicit initialization for Reasoning Engine stability
            from vertexai.generative_models import GenerativeModel, Content, Part
            sys_instr = Content(role="system", parts=[Part.from_text(self.system_prompt)])

            self._model = GenerativeModel(
                model_name=self.model_name,
                system_instruction=sys_instr,
            )
        return self._model

    def __call__(self, raw_text: str) -> Optional[Dict[str, Any]]:
        return self.filter_text(raw_text)

    def filter_text(self, raw_text: str) -> Optional[Dict[str, Any]]:
        from vertexai.generative_models import GenerationConfig
        print(f"DEBUG: Starting filter_text for input: {raw_text}", flush=True)

        source = (raw_text or "").strip()
        if not source:
            return {"corrected_text": ""}

        try:
            gen_config = GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                response_mime_type="application/json",
            )

            print(f"DEBUG: Calling Gemini model...", flush=True)
            response = self.model.generate_content(source, generation_config=gen_config)

            full_response_text = response.text.strip()
            print(f"DEBUG: Raw Model Output: \n{full_response_text}\n", flush=True)

            # Find the first '{' and the last '}'
            start_idx = full_response_text.find('{')
            end_idx = full_response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                return {"corrected_text": source}

            clean_json_str = full_response_text[start_idx:end_idx]

            # 3. Parsing the cleaned string
            parsed = json.loads(clean_json_str)

            # 4. Validation
            validated = TremorFilterResponse.model_validate(parsed)
            result = validated.model_dump()
            print(f"DEBUG: Validated Result: {result}", flush=True)

            return result

        except Exception as e:
            error_detail = traceback.format_exc()
            log.error(f"Tremor Agent Error: {error_detail}")

            return {
                "corrected_text": f"AGENT_CRASH: {str(e)}",
                "debug_info": error_detail[:200],
                "raw_response_captured": response.text if 'response' in locals() else "None"
            }