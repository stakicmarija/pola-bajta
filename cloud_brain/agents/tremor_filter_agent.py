from __future__ import annotations

import importlib
import json
import logging
from typing import Any

from pydantic import BaseModel, Field, ValidationError

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


# --- Pydantic response model ---

class TremorFilterResponse(BaseModel):
    corrected_text: str = Field(
        ...,
        description="The grammatically correct, cleaned sentence.",
    )


SYSTEM_PROMPT = """
You are TremorFilterAgent for an accessibility system.

Your goal is to reconstruct the most likely intended sentence from noisy, tremor-affected input.

The input may contain:
- misspellings
- repeated letters
- missing spaces
- broken or partial words
- accidental characters

Instructions:
- Convert the input into a clear, grammatically correct sentence.
- Correct obvious misspellings and keyboard errors.
- Normalize repeated letters into standard spelling (e.g. "pleaaaase" → "please").
- Merge or split words when necessary.
- Infer the most likely intended words when confidence is high.

Important constraints:
- Do NOT invent new meaning or change the user's intent.
- If multiple interpretations are possible, choose the most common and practical one.
- Prefer simple, common words over rare ones.
- Do not add extra information beyond what the user likely intended.

Return ONLY a JSON object with one field:
- "corrected_text": the cleaned sentence
""".strip()


class TremorFilterAgent:
    """LLM-based intent reconstruction for tremor-affected typed input."""

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

        if self._model is None and GenerativeModel is not None:
            self._model = GenerativeModel(
                model_name=self.model_name,
                system_instruction=SYSTEM_PROMPT,
            )

    def __call__(self, raw_text: str) -> TremorFilterResponse | None:
        return self.filter_text(raw_text)

    def filter_text(self, raw_text: str) -> TremorFilterResponse | None:
        """
        Returns a validated TremorFilterResponse, or None if the model is unavailable.
        Callers should fall back to raw_text if None is returned.
        """
        source = (raw_text or "").strip()
        if not source:
            return TremorFilterResponse(corrected_text="")

        if self._model is None:
            log.warning("Model unavailable, returning None.")
            return None

        try:
            kwargs: dict[str, Any] = {}
            if GenerationConfig is not None:
                kwargs["generation_config"] = GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_output_tokens,
                    response_mime_type="application/json",  # Forces JSON output
                )

            response = self._model.generate_content(source, **kwargs)
            raw_json = self._extract_text(response).strip()

            if not raw_json:
                log.warning("Empty response from model.")
                return None

            parsed = json.loads(raw_json)
            return TremorFilterResponse.model_validate(parsed)

        except json.JSONDecodeError as e:
            log.error("Failed to parse model JSON response: %s", e)
            return None
        except ValidationError as e:
            log.error("Response failed Pydantic validation: %s", e)
            return None
        except Exception as e:
            log.error("Unexpected error in filter_text: %s", e)
            return None

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

        first = candidates[0]
        content = getattr(first, "content", None)
        parts = getattr(content, "parts", None)
        if not parts:
            return ""

        return "\n".join(
            p.text for p in parts if isinstance(getattr(p, "text", None), str)
        ).strip()

