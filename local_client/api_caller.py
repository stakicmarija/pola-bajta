import requests
import json
import subprocess
import config

def get_google_auth_token():
    token = subprocess.check_output("gcloud auth print-access-token", shell=True)
    return token.decode('utf-8').strip()

URL = f"https://{config.LOCATION}-aiplatform.googleapis.com/v1/projects/{config.PROJECT_ID}/locations/{config.LOCATION}/endpoints/{config.ENDPOINT_ID}:predict"

def get_execution_plan(user_text, dom_snapshot):
    payload = {
        "instances": [
            {
                "user_query": user_text,
                "dom_elements": dom_snapshot 
            }
        ]
    }

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_google_auth_token()}"
        }

        print(f"Calling Vertex AI: '{user_text}'...")
        
        response = requests.post(URL, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        prediction = result['predictions'][0]
        
        # npr prediction = '{"selected_id": 12, "action": "click"}'
        if isinstance(prediction, str):
            return json.loads(prediction)
        
        return prediction

    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error: {err}")
        return {"error": "API communication failed", "details": str(err)}
    except Exception as e:
        print(f"Error in api_caller: {e}")
        return {"error": "Unknown error"}