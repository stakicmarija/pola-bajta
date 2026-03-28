import sys
import threading
import queue
import config
from playwright.sync_api import connect_over_cdp
from pynput import keyboard as pkb
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from local_client.ui import InputOverlay, ConfirmationOverlay
from local_client.api_caller import get_translation_voice, get_translation_text, get_execution_plan
from local_client.dom_parser import get_current_dom
from local_client.executor import execute_plan


events = queue.Queue()
_pressed = set()
_active_dialog = None


def hotkey_worker():
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


def on_dialog_done(dialog):
    global _active_dialog

    if not dialog.result:
        _active_dialog = None
        return

    if dialog.mode == "voice":
        response = get_translation_voice(dialog.result)
    else:
        response = get_translation_text(dialog.result)

    # show Agent 1 response to user
    confirm_dlg = ConfirmationOverlay(response["text"])
    confirm_dlg.exec()

    if confirm_dlg.confirmed:
        print("User confirmed!")
        with connect_over_cdp(config.CHROME_URL) as browser:
            context = browser.contexts[0].pages[0]
            dom_snapshot = get_current_dom(context)
            plan = get_execution_plan(response["text"], dom_snapshot, context.url)
            print(plan)
            execute_plan(plan, context)

    else:
        print("User rejected.")

    _active_dialog = None


def open_dialog(mode):
    """Open a dialog, closing any existing one first."""
    global _active_dialog

    # close existing dialog if open
    if _active_dialog is not None:
        _active_dialog.close()
        _active_dialog = None

    dlg = InputOverlay(mode=mode)
    dlg.finished.connect(lambda: on_dialog_done(dlg))
    _active_dialog = dlg
    dlg.show()
    dlg.raise_()
    dlg.activateWindow()


def process_events():
    while not events.empty():
        evt = events.get()
        if evt == "open_text":
            open_dialog("text")
        elif evt == "open_voice":
            open_dialog("voice")


def main():
    app = QApplication(sys.argv)

    t = threading.Thread(target=hotkey_worker, daemon=True)
    t.start()

    timer = QTimer()
    timer.timeout.connect(process_events)
    timer.start(50)

    print("Steady active.")
    print("Ctrl+Space = text")
    print("Alt+Space  = voice")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()