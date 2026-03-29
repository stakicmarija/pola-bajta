import base64
from typing import Dict, Any

class AccessibilityOrchestrator:
    def __init__(self):
        # Lazy imports for Cloud stability
        import agents.tremor_filter_agent as tremor
        import agents.voice_filter_agent as voice
        import agents.planner_agent as planner

        self.tremor_denoiser = tremor.TremorFilterAgent()
        self.voice_denoiser = voice.VoiceFilterAgent()
        self.planner = planner.DOMActionAgent()

    def query(self, request_type: str, **kwargs) -> Dict[str, Any]:
        if request_type == "clean":
            return self.clean_intent(
                input_type=kwargs.get("input_type"),
                payload=kwargs.get("payload")
            )
        elif request_type == "next_action":
            return self.get_next_action(
                clean_goal=kwargs.get("clean_goal"),
                elements=kwargs.get("elements", []),
                url=kwargs.get("url", "")
            )
        return {"error": "Invalid request_type. Use 'clean' or 'next_action'."}

    def clean_intent(self, input_type: str, payload: str) -> Dict[str, Any]:
        if input_type == "text":
            # REMOVED .model_dump() because tremor_denoiser now returns a dict
            result = self.tremor_denoiser.filter_text(payload)
            return result if result else {"corrected_text": payload}

        elif input_type == "audio":
            audio_bytes = base64.b64decode(payload)
            # REMOVED .model_dump() because voice_denoiser now returns a dict
            result = self.voice_denoiser.filter_audio_bytes(audio_bytes)
            return result if result else {"corrected_text": "Error transcribing audio"}

        return {"error": "Unknown input type"}

    def get_next_action(self, clean_goal: str, elements: list, url: str) -> Dict[str, Any]:
        # planner.next_action already returns a dict or None
        result = self.planner.next_action(clean_goal, elements, url)
        return result if result else {"error": "Could not determine next action", "done": True}