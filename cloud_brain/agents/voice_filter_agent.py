from __future__ import annotations

import importlib
import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

log = logging.getLogger(__name__)

GenerationConfig: Any | None = None
GenerativeModel: Any | None = None
Part: Any | None = None


def _ensure_vertex_classes() -> None:
    global GenerationConfig, GenerativeModel, Part
    if GenerationConfig is not None and GenerativeModel is not None and Part is not None:
        return

    try:
        module = importlib.import_module("vertexai.generative_models")
        GenerationConfig = getattr(module, "GenerationConfig", None)
        GenerativeModel = getattr(module, "GenerativeModel", None)
        Part = getattr(module, "Part", None)
    except Exception as e:
        log.error("Error loading Vertex SDK classes: %s", e)
        GenerationConfig = None
        GenerativeModel = None
        Part = None


class VoiceTranscriptionResponse(BaseModel):
    corrected_text: str = Field(
        ...,
        description="The transcribed and cleaned sentence from the audio input.",
    )


AUDIO_SYSTEM_PROMPT = """
You are VoiceFilterAgent for an accessibility system.

Your goal is to transcribe the provided audio and produce a clean, accurate sentence.

Instructions:
- Transcribe the spoken content accurately.
- Remove filler words (um, uh, like, you know) and repetitions.
- Fix obvious errors and produce a grammatically correct sentence.
- Preserve the speaker's original intent.

Return ONLY a JSON object with one field:
- "corrected_text": the cleaned transcription
""".strip()


class VoiceFilterAgent:
    """LLM-based transcription and cleanup for WAV audio input."""

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

        self._audio_model = model

        if GenerativeModel is not None and self._audio_model is None:
            self._audio_model = GenerativeModel(
                model_name=self.model_name,
                system_instruction=AUDIO_SYSTEM_PROMPT,
            )

    def _build_generation_config(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if GenerationConfig is not None:
            kwargs["generation_config"] = GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                response_mime_type="application/json",
            )
        return kwargs

    def filter_audio_bytes(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> VoiceTranscriptionResponse | None:
        if not audio_bytes:
            log.warning("Empty audio bytes provided.")
            return None

        if self._audio_model is None or Part is None:
            log.warning("Audio model or Part unavailable, returning None.")
            return None

        try:
            audio_part = Part.from_data(data=audio_bytes, mime_type=mime_type)
            response = self._audio_model.generate_content(audio_part, **self._build_generation_config())
            raw_json = self._extract_text(response).strip()

            if not raw_json:
                log.warning("Empty response from model for audio input.")
                return None

            parsed = json.loads(raw_json)
            return VoiceTranscriptionResponse.model_validate(parsed)

        except json.JSONDecodeError as e:
            log.error("Failed to parse model JSON response for audio: %s", e)
            return None
        except ValidationError as e:
            log.error("Audio response failed Pydantic validation: %s", e)
            return None
        except Exception as e:
            log.error("Unexpected error in filter_audio_bytes: %s", e)
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