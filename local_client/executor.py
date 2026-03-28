from playwright.sync_api import sync_playwright
import time
import config

def execute_plan(plan):
    selected_id = plan.get("selected_id")
    action = plan.get("action", "click").lower()
    text_to_type = plan.get("text_to_type", "")

    if selected_id is None:
        print("Executor: No valid ID in execution plan.")
        return False

    try:
        with sync_playwright().start() as p:
            browser = p.chromium.connect_over_cdp(config.CHROME_URL)
            context = browser.contexts[0]
            page = context.pages[0]

            selector = f'[{config.AI_ATTRIBUTE}="{selected_id}"]'
            element = page.wait_for_selector(selector, timeout=5000)
            
            if not element:
                print(f"Executor: Elem with ID {selected_id} not found.")
                return False

            if action == "click":
                print(f"Click elem, ID: {selected_id}")
                element.click()
            
            elif action == "type":
                print(f"Type '{text_to_type}' , elem ID: {selected_id}")
                element.fill(text_to_type)
                
            elif action == "scroll":
                element.scroll_into_view_if_needed()
            
            elif action == "hover":
                element.hover()
            
            print("Success.")
            return True

    except Exception as e:
        print(f"Executor error: {e}")
        return False