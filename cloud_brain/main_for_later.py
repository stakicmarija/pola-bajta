# import sys
# import threading
# import queue
# import local_client.config as config
# from playwright.sync_api import sync_playwright
# from pynput import keyboard as pkb
# from PyQt6.QtCore import QTimer
# from PyQt6.QtWidgets import QApplication
# from local_client.ui import InputOverlay, ConfirmationOverlay
# import local_client.api_caller as api_caller
# from local_client.api_caller import get_translation_voice, get_translation_text, get_execution_plan
# from local_client.dom_parser import get_current_dom
# from local_client.executor import execute_plan
# _global_page = None
#
#
# events = queue.Queue()
# _pressed = set()
# _active_dialog = None
#
#
# def hotkey_worker():
#     def on_press(key):
#         _pressed.add(key)
#
#         ctrl = pkb.Key.ctrl_l in _pressed or pkb.Key.ctrl_r in _pressed
#         alt = pkb.Key.alt in _pressed or pkb.Key.alt_l in _pressed or pkb.Key.alt_r in _pressed
#         space = pkb.Key.space in _pressed
#
#         if ctrl and space and not alt:
#             events.put("open_text")
#
#         if alt and space and not ctrl:
#             events.put("open_voice")
#
#     def on_release(key):
#         _pressed.discard(key)
#
#     with pkb.Listener(on_press=on_press, on_release=on_release) as listener:
#         listener.join()
#
#
# def on_dialog_done(dialog):
#     global _global_page
#
#     if not dialog.result: return
#
#     print("\n" + "=" * 50)
#     print(f"📡 STEP 1: Sending Raw Input to TremorFilterAgent...")
#     print(f"RAW INPUT: '{dialog.result}'")
#
#     # 1. Clean the initial messy intent
#     response = get_translation_text(dialog.result)
#
#     # Trace the "Cleaning" result
#     clean_goal = response.get("corrected_text", dialog.result)
#     print(f"✅ REFINED GOAL: '{clean_goal}'")
#     print("=" * 50 + "\n")
#
#     is_done = False
#     step_count = 0
#
#     while not is_done:
#         step_count += 1
#         print(f"--- 🔄 EXECUTION CYCLE #{step_count} ---")
#
#         dom_snapshot = get_current_dom(_global_page)
#
#         try:
#             plan = get_execution_plan(clean_goal, dom_snapshot, _global_page.url)
#             print(f"📥 PLAN RECEIVED: {plan}")
#         except Exception as e:
#             print(f"❌ CLOUD ERROR: {e}")
#             break
#
#         if not plan:
#             print("⚠️ No plan received. Stopping.")
#             break
#
#         # 1. Check if the AI is done WITHOUT an action
#         # (e.g., if the user says 'open mail' and it's already open)
#         if plan.get("done") and not plan.get("action"):
#             print("🏁 AI says we are already done.")
#             break
#
#         # 2. PROPOSE the action
#         action_type = plan.get('action', 'N/A')
#         element_id = plan.get('selected_id', 'N/A')
#
#         confirm_dlg = ConfirmationOverlay(f"Action: {action_type} on {element_id}\nProceed?")
#         confirm_dlg.exec()
#
#         if confirm_dlg.confirmed:
#             print(f"🚀 EXECUTING...")
#             execute_plan(plan, _global_page)
#
#             # 3. ONLY NOW DO WE EXIT if the AI said 'done'
#             if plan.get("done"):
#                 print("🏁 Action performed and AI signals final completion.")
#                 is_done = True
#
#             _global_page.wait_for_timeout(1000)  # Give the browser time to render
#         else:
#             print("🛑 User rejected action.")
#             break
#
#     print("=" * 50 + "\n")
#
#
# def open_dialog(mode):
#     """Open a dialog, closing any existing one first."""
#     global _active_dialog
#
#     # close existing dialog if open
#     if _active_dialog is not None:
#         _active_dialog.close()
#         _active_dialog = None
#
#     dlg = InputOverlay(mode=mode)
#     dlg.finished.connect(lambda: on_dialog_done(dlg))
#     _active_dialog = dlg
#     dlg.show()
#     dlg.raise_()
#     dlg.activateWindow()
#
#
# def process_events():
#     while not events.empty():
#         evt = events.get()
#         if evt == "open_text":
#             open_dialog("text")
#         elif evt == "open_voice":
#             open_dialog("voice")
#
#
# def main():
#     global _global_page, _playwright, _browser
#
#     app = QApplication(sys.argv)
#
#     print("System Booting: Connecting to Cloud Brain (Vertex AI)...")
#     api_caller.init_engine()
#
#     # This assertion ensures we don't proceed if the internet is down
#     if api_caller._remote_app is None:
#         print("CRITICAL ERROR: Could not connect to the Brain. Exiting.")
#         sys.exit(1)
#
#     print("Cloud Brain Connected. Initializing Browser...")
#
#     try:
#         # Now we initialize Playwright
#         _playwright = sync_playwright().start()
#         _browser = _playwright.chromium.connect_over_cdp(config.CHROME_URL)
#         _global_page = _browser.contexts[0].pages[0]
#
#         # Start the Hotkey Listener
#         t = threading.Thread(target=hotkey_worker, daemon=True)
#         t.start()
#
#         # Start UI Polling
#         timer = QTimer()
#         timer.timeout.connect(process_events)
#         timer.start(50)
#
#         print("--- SYSTEM READY ---")
#         print("The Agent is now live and hooked to Chrome.")
#
#         exit_code = app.exec()
#         _playwright.stop()
#         sys.exit(exit_code)
#
#     except Exception as e:
#         print(f"Startup Error: {e}")
#         sys.exit(1)
#
#
# if __name__ == "__main__":
#     main()

import sys
import os
import threading
import queue
import local_client.config as config
from playwright.sync_api import sync_playwright
from pynput import keyboard as pkb
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

# --- ROBUSTNESS: Ensure credentials are baked in ---
os.environ[
    "GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/nemanjaudovic/PycharmProjects/pola_bajta/pola-bajta/your_existing_key.json"

from local_client.ui import InputOverlay, ConfirmationOverlay
import local_client.api_caller as api_caller
from local_client.api_caller import get_translation_text, get_execution_plan
from local_client.dom_parser import get_current_dom
from local_client.executor import execute_plan

# Global state
_browser = None
_playwright = None
_active_dialog = None
events = queue.Queue()
_pressed = set()


def hotkey_worker():
    """Independent thread for low-level keyboard listening."""

    def on_press(key):
        _pressed.add(key)
        ctrl = pkb.Key.ctrl_l in _pressed or pkb.Key.ctrl_r in _pressed
        alt = pkb.Key.alt in _pressed or pkb.Key.alt_l in _pressed or pkb.Key.alt_r in _pressed
        space = pkb.Key.space in _pressed

        if ctrl and space and not alt:
            events.put("open_text")
        if alt and space and not ctrl:
            events.put("open_voice")

    def on_release(key):
        _pressed.discard(key)

    with pkb.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


def get_active_page():
    """Helper to ensure we are always interacting with the user's current tab."""
    global _browser
    try:
        # Get the most recently focused or created page
        pages = _browser.contexts[0].pages
        return pages[-1] if pages else None
    except Exception as e:
        print(f"❌ Failed to sync with browser tabs: {e}")
        return None


def on_dialog_done(dialog):
    """The Core Brain logic triggered when the user finishes typing/speaking."""
    if not dialog.result:
        return

    # 1. SYNC: Always grab the current tab
    page = get_active_page()
    if not page:
        print("❌ Error: No active browser page found.")
        return

    print(f"\n{'=' * 20} STARTING AGENT {'=' * 20}")
    print(f"📡 Page: {page.url[:50]}...")
    print(f"⌨️ Raw Input: '{dialog.result}'")

    # 2. REFINEMENT (Tremor Filter)
    try:
        response = get_translation_text(dialog.result)
        # Use .get() with a fallback to the original messy text if API fails
        clean_goal = response.get("corrected_text", dialog.result)
    except Exception as e:
        print(f"⚠️ Tremor API Error: {e}")
        clean_goal = dialog.result

    print(f"✅ Refined Goal: '{clean_goal}'\n")

    # 3. AUTONOMOUS LOOP
    step_count = 0
    max_steps = 10

    while step_count < max_steps:
        step_count += 1
        print(f"--- 🔄 Cycle #{step_count} ---")

        # Wait for page stability so we don't get an empty DOM
        try:
            page.wait_for_load_state("domcontentloaded", timeout=5000)
        except:
            pass

        dom_snapshot = get_current_dom(page)
        print(f"📸 Snapshot: {len(dom_snapshot)} elements found.")

        # A. Request Plan from Cloud
        try:
            plan = get_execution_plan(clean_goal, dom_snapshot, page.url)
            print(f"🧠 Plan: {plan}")
        except Exception as e:
            print(f"❌ Planner Error: {e}")
            break

        if not plan:
            break

        # B. Check for Termination
        if plan.get("done") and (not plan.get("action") or plan.get("action") == "wait"):
            print("🏁 Mission accomplished.")
            break

        # --- FIX: TRANSLATE ID TO HUMAN TEXT ---
        action = plan.get('action', 'wait')
        raw_id = plan.get('selected_id', 'N/A')

        # Determine the friendly name for the UI
        target_label = f"ID {raw_id}"
        if raw_id != 'N/A':
            try:
                # Clean the ID (handles 1.0 vs 1)
                clean_target_id = int(float(raw_id))
                # Look for this ID in our snapshot list
                for el in dom_snapshot:
                    if el.get('id') == clean_target_id:
                        # Grab text, placeholder, or role to describe it
                        element_text = el.get('text', '').strip() or el.get('role', '')
                        if element_text:
                            target_label = f"'{element_text}'"
                        break
            except (ValueError, TypeError):
                pass

        # C. PROPOSE ACTION (Human Readable)
        proposal_msg = f"AI wants to: {action.upper()} on {target_label}\nProceed?"
        confirm = ConfirmationOverlay(proposal_msg)

        # Trigger a "pre-action" flash in the browser so the user sees what's being discussed
        # Note: Ensure execute_plan has a sub-function or logic to highlight the element
        if raw_id != 'N/A':
            # We call a small script to highlight the element BEFORE the dialog blocks execution
            try:
                selector = f'[data-ai-id="{int(float(raw_id))}"]'
                page.evaluate(f"""(sel) => {{
                    const el = document.querySelector(sel);
                    if (el) {{
                        el.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                        el.style.outline = '5px solid #FF3B30';
                        el.style.boxShadow = '0 0 20px #FF3B30';
                        setTimeout(() => {{ el.style.outline = ''; el.style.boxShadow = ''; }}, 2000);
                    }}
                }}""", selector)
            except:
                pass

        confirm.exec()  # This blocks until user clicks

        if confirm.confirmed:
            print(f"🚀 Executing {action}...")
            execute_plan(plan, page)

            if plan.get("done"):
                print("🏁 Final action completed.")
                break

            page.wait_for_timeout(1000)
        else:
            print("🛑 User aborted sequence.")
            break

    print(f"{'=' * 50}\n")


def process_events():
    """Polls the hotkey queue and opens UI."""
    while not events.empty():
        evt = events.get()
        # Ensure we close old ones to prevent focus stealing
        global _active_dialog
        if _active_dialog:
            _active_dialog.close()

        dlg = InputOverlay(mode=("voice" if evt == "open_voice" else "text"))
        dlg.finished.connect(lambda: on_dialog_done(dlg))
        _active_dialog = dlg
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()


def main():
    global _playwright, _browser

    app = QApplication(sys.argv)

    print("🧠 Booting Cloud Brain...")
    api_caller.init_engine()
    if api_caller._remote_app is None:
        print("❌ Connection Failed. Check internet/credentials.")
        return

    print("🌐 Connecting to Chrome Debugger...")
    try:
        _playwright = sync_playwright().start()
        # Connect to your script-launched Chrome
        _browser = _playwright.chromium.connect_over_cdp(config.CHROME_URL)

        # Start input listeners
        threading.Thread(target=hotkey_worker, daemon=True).start()

        # UI Event Loop Link
        timer = QTimer()
        timer.timeout.connect(process_events)
        timer.start(50)

        print("🚀 SYSTEM READY (Ctrl+Space for Text, Alt+Space for Voice)")
        sys.exit(app.exec())

    except Exception as e:
        print(f"❌ Startup Error: {e}")
    finally:
        if _playwright:
            _playwright.stop()


if __name__ == "__main__":
    main()