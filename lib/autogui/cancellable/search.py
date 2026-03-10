import time

import pyautogui
from autogui import CancellableAutogui


def locate_center_on_screen(gui: CancellableAutogui, image, timeout: float = 0, **kwargs):
    start = time.time()

    while True:
        gui._check()

        location = pyautogui.locateCenterOnScreen(image, **kwargs)
        if location is not None:
            break

        if timeout and time.time() - start >= timeout:
            raise TimeoutError(f"Image '{image}' not found within {timeout}s")

        time.sleep(gui._poll)

    return location
