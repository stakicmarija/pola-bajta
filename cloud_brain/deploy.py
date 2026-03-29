import vertexai
from vertexai.preview import reasoning_engines
# Use a relative import or ensure the class is picked up correctly
import agent

vertexai.init(
    project="polabajta",
    location="us-central1",
    staging_bucket="gs://polabajta"
)

print("📦 Packaging REAL agent with local context...")

# Define the instance from the imported module
orchestrator = agent.AccessibilityOrchestrator()

remote_app = reasoning_engines.ReasoningEngine.create(
    orchestrator,
    requirements=[
        "google-cloud-aiplatform[reasoningengine]",
        "cloudpickle==3.0.0",
        "google-cloud-storage",
        "langchain",
        "langchain-google-vertexai",
    ],
    # ⬇️ THIS IS THE CRITICAL CHANGE ⬇️
    # We include 'agent.py' directly so the cloud can 'find' the module
    extra_packages=["agents", "agent.py"],
    display_name="Accessibility_Orchestrator_Prod"
)

print(f"✅ DEPLOYMENT SUCCESSFUL! ID: {remote_app.resource_name}")