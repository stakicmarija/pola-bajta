# agent.py
import vertexai
from agents.tremor_filter_agent import tremor_agent
from agents.voice_filter_agent import voice_agent


class AccessibilityOrchestrator:
    def __init__(self):
        """
        This runs ONCE when the agent is deployed.
        You can initialize models or agents here.
        """
        self.tremor_agent = tremor_agent
        self.voice_agent = voice_agent

    def query(self, user_input: str, dom_context: str, input_type: str = "tremor"):
        """
        This is the main function called by your Local Client.
        It receives the messy text and the DOM.
        """
        # Logic to choose which agent to use
        if input_type == "voice":
            response = self.voice_agent.query(input=f"DOM: {dom_context}\nText: {user_input}")
        else:
            # Default to tremor agent
            response = self.tremor_agent.query(input=f"DOM: {dom_context}\nText: {user_input}")

        # This returns the JSON/Pydantic object your friend defined in their agents
        return response