import vertexai
from vertexai.preview import reasoning_engines
import config
import json

vertexai.init(project=config.PROJECT_ID, location=config.LOCATION)

def get_execution_plan(user_text, dom_snapshot):
    try:
        remote_app = reasoning_engines.ReasoningEngine(config.RESOURCE_NAME)
        response = remote_app.query(
            user_input=user_text,
            dom_context=json.dumps(dom_snapshot)
        )
        return response
    except Exception as e:
        print(f"Error: {e}")
        return {"error": "Cloud connection failed"}