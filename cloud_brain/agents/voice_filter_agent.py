from __future__ import annotations

import json
import importlib
import re
from typing import Any

GenerationConfig: Any | None = None
GenerativeModel: Any | None = None


def _ensure_vertex_classes() -> None:
	"""Load Vertex SDK classes lazily to keep local dev environment optional."""
	global GenerationConfig, GenerativeModel
	if GenerationConfig is not None and GenerativeModel is not None:
		return

	try:
		module = importlib.import_module("vertexai.generative_models")
		GenerationConfig = getattr(module, "GenerationConfig", None)
		GenerativeModel = getattr(module, "GenerativeModel", None)
	except Exception:
		GenerationConfig = None
		GenerativeModel = None


SYSTEM_PROMPT = """
You are VoiceFilterAgent for an accessibility pipeline.

Task:
- Input is noisy speech-to-text with fillers, repetition, false starts, and disfluency.
- Rewrite into clear, concise text while preserving user intent and meaning.

Rules:
- Remove filler words and repeated fragments when they do not change meaning.
- Do not add new facts, commands, or assumptions.
- Keep the same language as the input.
- Return ONLY the cleaned text, with no JSON, markdown, labels, or explanation.
""".strip()


class VoiceFilterAgent:
	"""Black-box text cleaner for voice-transcribed input."""

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

	def __call__(self, raw_text: str) -> str:
		return self.filter_text(raw_text)

	def filter_text(self, raw_text: str) -> str:
		"""Return cleaned text only. Never raises for runtime generation failures."""
		source = (raw_text or "").strip()
		if not source:
			return ""

		if self._model is None:
			return self._fallback_clean(source)

		prompt = (
			"Clean this voice-transcribed input. Return only cleaned text:\n\n"
			f"{source}"
		)

		try:
			kwargs: dict[str, Any] = {}
			if GenerationConfig is not None:
				kwargs["generation_config"] = GenerationConfig(
					temperature=self.temperature,
					max_output_tokens=self.max_output_tokens,
				)

			response = self._model.generate_content(prompt, **kwargs)
			cleaned = self._normalize_output(self._extract_text(response))
			return cleaned or self._fallback_clean(source)
		except Exception:
			return self._fallback_clean(source)

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

		texts: list[str] = []
		for part in parts:
			piece = getattr(part, "text", None)
			if isinstance(piece, str):
				texts.append(piece)
		return "\n".join(texts).strip()

	@staticmethod
	def _normalize_output(text: str) -> str:
		cleaned = (text or "").strip()
		if not cleaned:
			return ""

		cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
		cleaned = re.sub(r"\s*```$", "", cleaned).strip()

		if cleaned.startswith("{") and cleaned.endswith("}"):
			try:
				payload = json.loads(cleaned)
				for key in ("cleaned_text", "text", "output", "result"):
					value = payload.get(key)
					if isinstance(value, str):
						cleaned = value.strip()
						break
			except Exception:
				pass

		if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
			cleaned = cleaned[1:-1].strip()

		cleaned = re.sub(r"\s+", " ", cleaned).strip()
		return cleaned

	@staticmethod
	def _fallback_clean(text: str) -> str:
		"""Conservative fallback if model is unavailable or fails."""
		cleaned = text
		fillers_pattern = (
			r"\b(um+|uh+|erm|ah+|like|you know|i mean|sort of|kind of|basically|actually)\b"
		)
		cleaned = re.sub(fillers_pattern, " ", cleaned, flags=re.IGNORECASE)
		cleaned = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", cleaned, flags=re.IGNORECASE)
		cleaned = re.sub(r"\s+", " ", cleaned).strip()
		cleaned = re.sub(r"\s+([,.!?])", r"\1", cleaned)
		return cleaned


if __name__ == "__main__":
	agent = VoiceFilterAgent(model=None)
	sample = "um can you like open open the settings uh page please"
	print(agent.filter_text(sample))
