CHROME_DEBUG_PORT = 9222
CHROME_URL = f"http://localhost:{CHROME_DEBUG_PORT}"

# Google Cloud podaci iz deploy.py
PROJECT_ID = "polabajta"
LOCATION = "us-central1"            

# gemini sta sme da vrati
ALLOWED_ACTIONS = ["click", "type", "scroll", "wait", "hover", "enter", "back", "clear"]

AI_ATTRIBUTE = "data-ai-id"
RESOURCE_NAME = "projects/400778473557/locations/us-central1/reasoningEngines/1338994606154448896"