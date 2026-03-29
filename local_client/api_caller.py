import vertexai
from vertexai.preview import reasoning_engines
from . import config
import json
import base64
import sys

# 1. Immediate Init (Non-blocking SDK setup)
vertexai.init(project=config.PROJECT_ID, location=config.LOCATION)

# 2. Global variable to hold the live cloud connection
_remote_app = None


def init_engine():
    global _remote_app
    print(f"🔗 Attempting connection to: {config.RESOURCE_NAME}")
    try:
        # Remove the background thread logic for a moment to test
        _remote_app = reasoning_engines.ReasoningEngine(config.RESOURCE_NAME)

        # TEST CALL: Verify the engine actually responds
        test = _remote_app.query(request_type="clean", input_type="text", payload="test")
        print("✅ CLOUD BRAIN ONLINE AND RESPONDING")
    except Exception as e:
        print(f"❌ CRITICAL CONNECTION FAILURE: {e}")
        # If this fails, we want the whole app to stop so we can fix the ID
        sys.exit(1)


def get_translation_voice(audio_bytes):
    if _remote_app is None: return {"error": "Engine not ready"}

    encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")

    # Change: Use .query() and pass a 'request_type' flag
    return _remote_app.query(
        request_type="clean",
        input_type="audio",
        payload=encoded_audio
    )


def get_translation_text(input_str):
    #if _remote_app is None: return {"corrected_text": input_str}

    # Change: Use .query()
    return _remote_app.query(
        request_type="clean",
        input_type="text",
        payload=input_str
    )


# Global variable to hold the breadcrumb within a single user request
_last_action_summary = "None (This is the start of the task)"


def get_execution_plan(user_text, dom_snapshot, current_url, is_first_step=False):
    """
    Sends the goal, DOM, and URL to the Cloud, now including a
    'breadcrumb' of the last action to prevent repetitive loops.
    """
    global _last_action_summary, _remote_app

    if _remote_app is None:
        return {"error": "Engine not ready"}

    # Reset memory if this is a brand new hotkey trigger
    if is_first_step:
        _last_action_summary = "None (This is the start of the task)"

    try:

        contextual_goal = f"{user_text} | PREVIOUS STEP: {_last_action_summary}"

        response = _remote_app.query(
            request_type="next_action",
            clean_goal=contextual_goal,
            elements=dom_snapshot,
            url=current_url
        )

        # Update the breadcrumb for the NEXT cycle
        if response and not response.get("error"):
            act = response.get("action", "unknown")
            tid = response.get("selected_id", "N/A")
            _last_action_summary = f"Performed {act} on ID {tid}"

        return response

    except Exception as e:
        print(f"Planning Error: {e}")
        return {"error": "Cloud reasoning failed"}