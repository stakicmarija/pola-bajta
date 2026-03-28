import vertexai
from vertexai.preview import reasoning_engines
from agent import AccessibilityOrchestrator # Import your orchestrated class

# 1. Initialize your personal Google Cloud Project
vertexai.init(
    project="your-personal-project-id",
    location="us-central1",
    staging_bucket="gs://your-gcs-bucket-name" # Create a standard Cloud Storage bucket first
)

print("Packaging agents and deploying to Vertex AI...")

# 2. The Deployment Command
remote_app = reasoning_engines.ReasoningEngine.create(
    AccessibilityOrchestrator(),
    display_name="Parkinsons_Accessibility_Agent",
    description="Multi-agent ADK pipeline for UI translation",
    requirements=[
        "google-adk",
        "pydantic",
        "google-cloud-aiplatform"
    ]
)

print(f"Deployment Complete! Your Agent ID is: {remote_app.resource_name}")