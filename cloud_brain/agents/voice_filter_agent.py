import json
import logging
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class VoiceTranscriptionResponse(BaseModel):
    corrected_text: str = Field(..., description="The transcribed sentence.")


class VoiceFilterAgent:
    def __init__(
            self,
            model_name: str = "gemini-2.5-flash",
            temperature: float = 0.4,
            max_output_tokens: int = 256,
    ) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self._model = None

        # Internalize the prompt
        self.system_prompt = """
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

    @property
    def model(self):
        if self._model is None:
            from vertexai.generative_models import GenerativeModel
            self._model = GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_prompt,
            )
        return self._model

    def filter_audio_bytes(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> Optional[Dict[str, Any]]:
        # Import Vertex classes LOCALLY inside the method
        from vertexai.generative_models import GenerationConfig, Part

        if not audio_bytes:
            return {"corrected_text": ""}

        try:
            # 1. Prepare Audio Part
            audio_part = Part.from_data(data=audio_bytes, mime_type=mime_type)

            # 2. Setup Config
            gen_config = GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                response_mime_type="application/json",
            )

            # 3. Generate
            response = self.model.generate_content(
                audio_part,
                generation_config=gen_config
            )

            # 4. Parse and Validate
            raw_json = response.text.strip()
            parsed = json.loads(raw_json)
            validated = VoiceTranscriptionResponse.model_validate(parsed)

            return validated.model_dump()

        except Exception as e:
            log.error(f"Voice Agent Error: {e}")
            return {"corrected_text": "Error transcribing audio"}


