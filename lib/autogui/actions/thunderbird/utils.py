"""
Utility functions for Thunderbird usage
-
Prerequisites:
"""

import os

import pyautogui

from lib.autogui.search import locate_center_on_screen
from lib.task_manager.task_manager import get_gui, task

PARENT_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))


@task
def open_thunederbird(timeout: float = 5, **kwargs):
    gui = get_gui()

    location = gui.start(
        "find_thunderbird",
        lambda: locate_center_on_screen._func(
            os.path.join(PARENT_DIR, "thunderbird.png"), timeout=timeout, confidence=0.6, grayscale=True, **kwargs
        ),
    )

    pyautogui.click(location.value)
