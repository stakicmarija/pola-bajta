import os
import json
import cloudpickle
# Ensure the path matches your folder structure
from cloud_brain.agents.planner_agent import DOMActionAgent

# 1. Setup Credentials
os.environ[
    "GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/nemanjaudovic/PycharmProjects/pola_bajta/pola-bajta/your_existing_key.json"


def test_planner_logic():
    print("🚀 Testing DOMActionAgent Locally...")
    agent = DOMActionAgent()

    # Mock Data: Simulating a simple Login Page
    mock_intent = "click the login button"
    mock_url = "https://example.com/login"
    mock_elements = [
        {"id": 101, "tag": "input", "text": "", "role": "textbox"},  # Username
        {"id": 102, "tag": "input", "text": "", "role": "password"},  # Password
        {"id": 103, "tag": "button", "text": "Sign In", "role": "button"},  # The Target
        {"id": 104, "tag": "a", "text": "Forgot Password?", "role": "link"}
    ]

    print(f"Intent: {mock_intent}")
    print(f"Elements provided: {len(mock_elements)}")

    try:
        # Call the agent
        result = agent.next_action(
            corrected_text=mock_intent,
            elements=mock_elements,
            current_url=mock_url
        )

        print("\n--- AGENT RESPONSE ---")
        print(json.dumps(result, indent=2))

        # Validation Check
        if result and result.get("selected_id") == 103:
            print("\n✅ SUCCESS: Agent correctly identified the 'Sign In' button (ID 103).")
        else:
            print("\n⚠️ WARNING: Agent picked the wrong ID or failed.")

    except Exception as e:
        print(f"\n❌ CRITICAL FAILURE: {e}")


def check_serialization():
    print("\n📦 Checking Cloud Compatibility (Serialization)...")
    agent = DOMActionAgent()
    try:
        serialized = cloudpickle.dumps(agent)
        print("✅ SUCCESS: Agent is ready for Cloud deployment.")
    except Exception as e:
        print(f"❌ SERIALIZATION ERROR: {e}")


if __name__ == "__main__":
    test_planner_logic()
    check_serialization()