CHROME_DEBUG_PORT = 9222
CHROME_URL = f"http://localhost:{CHROME_DEBUG_PORT}"

# Google Cloud podaci iz deploy.py
PROJECT_ID = "glass-core-461803-v7" 
LOCATION = "us-central1"            

# gemini sta sme da vrati
ALLOWED_ACTIONS = ["click", "type", "scroll", "wait", "hover", "enter", "back", "clear"]

AI_ATTRIBUTE = "data-ai-id"
RESOURCE_NAME = "projects/glass-core-461803-v7/locations/us-central1/reasoningEngines/TVOJ_ID"
 