import config

def execute_plan(plan, page):
    if not plan or "error" in plan:
        print("Executor: Plan je neispravan.")
        return False

    selected_id = plan.get("selected_id")
    action = str(plan.get("action", "")).lower()
    text_to_type = plan.get("text_to_type", "")

    if selected_id is None and action not in ["back", "enter", "wait"]:
        print("Executor: no id for action.")
        return False

    try:
        selector = f'[{config.AI_ATTRIBUTE}="{selected_id}"]'
        
        if action == "click":
            element = page.wait_for_selector(selector, timeout=5000)
            print(f"Click ID: {selected_id}")
            element.click(force=True)
        
        elif action == "type":
            element = page.wait_for_selector(selector, timeout=5000)
            print(f"Typing '{text_to_type}' to ID: {selected_id}")
            element.fill(text_to_type)
            
        elif action == "scroll":
            element = page.wait_for_selector(selector, timeout=5000)
            element.scroll_into_view_if_needed()
        
        elif action == "hover":
            element = page.wait_for_selector(selector, timeout=5000)
            element.hover()

        elif action == "enter":
            page.keyboard.press("Enter")

        elif action == "clear":
            element = page.wait_for_selector(selector, timeout=5000)
            element.clear()
        
        elif action == "wait":
            page.wait_for_timeout(2000)

        elif action == "back":
            page.go_back()

        print("Action executed.")
        return True

    except Exception as e:
        print(f"Error in executor: {e}")
        return False