# deploy.py
import vertexai
from vertexai.preview import reasoning_engines
from agent import AccessibilityOrchestrator # This now points to your class above

vertexai.init(
    project="glass-core-461803-v7",
    location="us-central1",
    staging_bucket="gs://my-hackathon-code-123" # <--- Update this!
)

print("Packaging agents and deploying to Vertex AI...")

# This command "bundles" your agent.py and agents/ folder
remote_app = reasoning_engines.ReasoningEngine.create(
    AccessibilityOrchestrator(), # This instantiates your class
    display_name="Parkinsons_Accessibility_Agent",
    requirements=[
        "google-adk",
        "pydantic",
        "google-cloud-aiplatform[reasoning_engines,preview]"
    ]
)

print(f"Deployment Complete! Your Agent ID is: {remote_app.resource_name}")