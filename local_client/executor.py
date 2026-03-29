from . import config

def flash_element(page, selector, duration=3000):
    """
    Injects a CSS highlight to show the user actly where the AI is acting.
    Increased duration to allow users with tremors more time to visually track.
    """
    try:
        page.evaluate(f"""
            (sel) => {{
                const el = document.querySelector(sel);
                if (el) {{
                    const originalTransition = el.style.transition;
                    el.style.transition = 'all 0.2s ease-in-out';
                    el.style.outline = '5px solid #007AFF';
                    el.style.boxShadow = '0 0 25px #007AFF';
                    el.style.transform = 'scale(1.05)';
                    el.style.zIndex = '9999'; // Ensure it stays on top

                    setTimeout(() => {{
                        el.style.outline = '';
                        el.style.boxShadow = '';
                        el.style.transform = '';
                        el.style.transition = originalTransition;
                    }}, {duration});
                }}
            }}
        """, selector)
    except:
        pass

def execute_plan(plan, page):
    if not plan or "error" in plan:
        print("Executor: Plan is invalid.")
        return False

    raw_id = plan.get("selected_id")
    action = str(plan.get("action", "")).lower()
    text_to_type = plan.get("text_to_type", "")

    selected_id = None
    if raw_id is not None:
        try:
            selected_id = str(int(float(raw_id)))
        except (ValueError, TypeError):
            selected_id = str(raw_id)

    needs_id = action in ["click", "type", "scroll", "hover", "clear"]
    if needs_id and selected_id is None:
        return False

    try:
        selector = f'[{config.AI_ATTRIBUTE}="{selected_id}"]' if selected_id else None
        print(f"🚀 Executing: {action.upper()} | Target ID: {selected_id or 'N/A'}")

        # Flash for 3 seconds instead of 0.8
        if selector:
            flash_element(page, selector, duration=3000)

        if action == "click":
            element = page.wait_for_selector(selector, timeout=5000)
            element.click(force=True)

        elif action == "type":
            element = page.wait_for_selector(selector, timeout=5000)
            element.fill(text_to_type)

        elif action == "scroll":
            element = page.wait_for_selector(selector, timeout=5000)
            element.scroll_into_view_if_needed()

        elif action == "hover":
            element = page.wait_for_selector(selector, timeout=5000)
            element.hover()
            page.wait_for_timeout(3000)

        elif action == "enter":
            if selector:
                element = page.wait_for_selector(selector, timeout=2000)
                element.press("Enter")
            else:
                page.keyboard.press("Enter")

        elif action == "clear":
            element = page.wait_for_selector(selector, timeout=5000)
            element.clear()

        elif action == "wait":
            page.wait_for_timeout(2000)

        elif action == "back":
            page.go_back()

        print("✅ Action executed successfully.")
        return True

    except Exception as e:
        print(f"❌ Error in executor: {e}")
        return False