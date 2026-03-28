from pydantic import BaseModel, Field
from google.adk.agents import Agent

# 1. Define the exact JSON structure your local laptop needs to execute the click
class UIAction(BaseModel):
    intent_summary: str = Field(description="A clean summary of the action.")
    css_selector: str = Field(description="The exact HTML CSS selector to click.")
    text_to_type: str | None = Field(description="Text to type into the element, or null.")

# 2. Build Agent 1: The Tremor Filter
tremor_filter_agent = Agent(
    name="tremor_filter",
    model="gemini-2.5-flash", # Flash is cheap and insanely fast for text
    instruction="""
    You are a kinetic tremor filter. The user has Parkinson's disease. 
    They will input text with double keystrokes, missed spaces, and phonetic errors.
    Your ONLY job is to decipher their raw intent and output a clean, single sentence.
    Example: 'snd eml tto saarahh' -> 'Send an email to Sarah'.
    """
)

# 3. Build Agent 2: The DOM UI Planner
ui_planner_agent = Agent(
    name="ui_planner",
    model="gemini-2.5-flash", # Flash has a 1M token context window, perfect for massive HTML DOMs
    instruction="""
    You are an expert UI automation engineer. 
    You will receive a user's clean intent and the raw HTML DOM of their current screen.
    Find the exact HTML element that matches their intent and return the CSS selector.
    """,
    response_model=UIAction # This forces Vertex AI to return our Pydantic JSON structure!
)


class AccessibilityOrchestrator:
    def __init__(self):
        # Load the agents into the orchestrator's memory
        self.filter = tremor_filter_agent
        self.planner = ui_planner_agent

    def query(self, messy_text: str, html_dom: str) -> dict:
        """
        This is the endpoint Vertex AI will expose.
        It orchestrates the handoff between Agent 1 and Agent 2.
        """

        # Step 1: Pass the messy text to the Tremor Filter Agent
        print(f"Original input: {messy_text}")
        clean_intent = self.filter(messy_text)
        print(f"Cleaned intent: {clean_intent}")

        # Step 2: Combine the clean text with the DOM, and pass to the Planner Agent
        planner_prompt = f"User Intent: {clean_intent}\n\nScreen HTML DOM:\n{html_dom}"

        # Because we set response_model=UIAction, this returns a Pydantic object
        action_plan = self.planner(planner_prompt)

        # Step 3: Convert the Pydantic object to a standard Python dictionary to send back to the user's laptop
        return action_plan.model_dump()