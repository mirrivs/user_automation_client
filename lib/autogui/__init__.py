import pyautogui

from lib.cancellable_futures import check, sleep


def write(message: str, interval: float = 0):
    """Cancellation-aware replacement for ``pyautogui.write()``.

    Checks for cancellation before each keystroke so long strings
    can be interrupted promptly instead of blocking until finished.
    """
    for char in message:
        check()
        pyautogui.press(char)
        if interval:
            sleep(interval)


def locate_image_center(image, timeout=10, **kwargs):
    import time

    import pyautogui

    start = time.monotonic()
    while True:
        check()
        loc = pyautogui.locateCenterOnScreen(image, **kwargs)
        if loc:
            return loc
        if time.monotonic() - start >= timeout:
            raise TimeoutError(f"'{image}' not found")
        sleep(0.1)
