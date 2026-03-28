# Takes intended action and DOM content and outputs next actionfrom __future__ import annotations

import importlib
import json
import logging
from typing import Any, Literal

from pydantic import BaseModel, ValidationError, model_validator

log = logging.getLogger(__name__)

GenerationConfig: Any | None = None
GenerativeModel: Any | None = None


def _ensure_vertex_classes() -> None:
    global GenerationConfig, GenerativeModel
    if GenerationConfig is not None and GenerativeModel is not None:
        return
    try:
        module = importlib.import_module("vertexai.generative_models")
        GenerationConfig = getattr(module, "GenerationConfig", None)
        GenerativeModel = getattr(module, "GenerativeModel", None)
    except Exception as e:
        log.error("Error loading Vertex SDK classes: %s", e)
        GenerationConfig = None
        GenerativeModel = None


class InteractiveElement(BaseModel):
    id: int
    tag: str
    text: str
    role: str


ActionType = Literal["click", "type", "scroll", "wait", "hover", "enter", "back", "clear"]
ELEMENT_TARGETING_ACTIONS: tuple[ActionType, ...] = ("click", "type", "scroll", "hover", "enter", "clear")


class Action(BaseModel):
    action: ActionType
    selected_id: int | None = None
    text_to_type: str | None = None
    done: bool

    @model_validator(mode="after")
    def check_fields(self) -> Action:
        if self.action in ELEMENT_TARGETING_ACTIONS:
            if self.selected_id is None:
                raise ValueError(f"'selected_id' is required for '{self.action}'.")
        elif self.selected_id is not None:
            raise ValueError(f"'selected_id' must be omitted for '{self.action}'.")

        if self.action == "type" and self.text_to_type is None:
            raise ValueError("'text_to_type' is required for type (use '' if empty).")
        if self.action != "type" and self.text_to_type is not None:
            raise ValueError("'text_to_type' must be omitted unless action is 'type'.")
        return self

SYSTEM_PROMPT = """
You are DOMActionAgent for a browser accessibility extension.

You receive:
1. USER INTENT — a clean sentence of what the user wants to do.
2. CURRENT URL — the page the user is currently on.
3. INTERACTIVE ELEMENTS — a JSON array of interactive elements on the current page.
   Each element has: id (integer), tag, text, role.

Return the single best next action to take right now.

## Action types

"click"    → selected_id required
"type"     → selected_id + text_to_type required (use "" if nothing to type yet)
"scroll"   → selected_id required
"hover"    → selected_id required
"enter"    → selected_id required
"clear"    → selected_id required
"wait"     → no extra fields needed
"back"     → no extra fields needed

## Rules
- Return exactly ONE action — the most logical immediate next step.
- Use only these actions: click, type, scroll, wait, hover, enter, back, clear.
- Use "wait" if you need to observe page changes before deciding the next step.
- Use "back" only when the best next move is returning to the previous page/state.
- Set done: true if this action fully completes the intent, false if more steps follow.
""".strip()


class DOMActionAgent:

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.0,
        max_output_tokens: int = 256,
        model: Any | None = None,
    ) -> None:
        _ensure_vertex_classes()
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self._model = model
        self._response_schema = Action.model_json_schema()

        if self._model is None and GenerativeModel is not None:
            self._model = GenerativeModel(
                model_name=self.model_name,
                system_instruction=SYSTEM_PROMPT,
            )

    def __call__(
        self,
        corrected_text: str,
        elements: list[dict[str, Any]],
        current_url: str = "",
    ) -> Action | None:
        return self.next_action(corrected_text, elements, current_url)

    def next_action(
        self,
        corrected_text: str,
        elements: list[dict[str, Any]],
        current_url: str = "",
    ) -> Action | None:
        intent = (corrected_text or "").strip()

        if not intent or not elements:
            log.warning("Empty intent or elements.")
            return None

        try:
            validated_elements = [InteractiveElement.model_validate(e) for e in elements]
        except ValidationError as e:
            log.error("Invalid elements input: %s", e)
            return None

        if self._model is None:
            log.warning("Model unavailable.")
            return None

        try:
            kwargs: dict[str, Any] = {}
            if GenerationConfig is not None:
                kwargs["generation_config"] = GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_output_tokens,
                    response_mime_type="application/json",
                    response_schema=self._response_schema,  # ← Pydantic drives the format
                )

            response = self._model.generate_content(
                self._build_prompt(intent, validated_elements, current_url),
                **kwargs,
            )
            raw_json = self._extract_text(response).strip()

            if not raw_json:
                log.warning("Empty response from model.")
                return None

            action = Action.model_validate(json.loads(raw_json))

            if action.selected_id is not None:
                valid_ids = {e.id for e in validated_elements}
                if action.selected_id not in valid_ids:
                    log.error("Model returned unknown element id %d.", action.selected_id)
                    return None

            return action

        except json.JSONDecodeError as e:
            log.error("Failed to parse JSON response: %s", e)
            return None
        except ValidationError as e:
            log.error("Response failed Pydantic validation: %s", e)
            return None
        except Exception as e:
            log.error("Unexpected error: %s", e)
            return None

    @staticmethod
    def _build_prompt(
        intent: str,
        elements: list[InteractiveElement],
        current_url: str,
    ) -> str:
        url_line = f"CURRENT URL:\n{current_url}\n\n" if current_url else ""
        return (
            f"USER INTENT:\n{intent}\n\n"
            f"{url_line}"
            f"INTERACTIVE ELEMENTS:\n"
            f"{json.dumps([e.model_dump() for e in elements], ensure_ascii=False, indent=2)}"
        )

    @staticmethod
    def _extract_text(response: Any) -> str:
        if response is None:
            return ""
        direct = getattr(response, "text", None)
        if isinstance(direct, str):
            return direct
        candidates = getattr(response, "candidates", None)
        if not candidates:
            return ""
        content = getattr(candidates[0], "content", None)
        parts = getattr(content, "parts", None)
        if not parts:
            return ""
        return "\n".join(
            p.text for p in parts if isinstance(getattr(p, "text", None), str)
        ).strip()

