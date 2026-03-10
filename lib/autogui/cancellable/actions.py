import pyautogui

from lib.autogui.cancellable.autogui import CancellableAutogui


def write(gui: CancellableAutogui, message: str, interval: float = 0):
    for c in message:
        gui._check()
        pyautogui.press(c.lower() if len(c) > 1 else c)
        gui.sleep(interval)
