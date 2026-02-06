"""
Utility functions for MS office on Windows
-
Prerequisites:
    - Windows operating system
    - MS Office installed
"""

import sys
import time
import os
import pyautogui as pag


from app_logger import app_logger

PARENT_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))


def start_app(app="word"):
    """
    Open app\n
    """
    try:
        pag.press("win")
        time.sleep(0.5)
        pag.write(app, 0.1)

        image = None
        app_image_mapping = {
            "word": "explorer_word.png",
            "excel": "explorer_excel.png",
            "powerpoint": "explorer_powerpoint.png",
        }
        image = os.path.join(PARENT_DIR, app_image_mapping.get(app, ""))

        if image:
            app_image = pag.locateCenterOnScreen(image, minSearchTime=5, confidence=0.8, grayscale=True)
            pag.click(app_image)
            pag.press("enter")
        else:
            raise ValueError("Invalid app name.")

        # Wait for office app identifier to be displayed - app is opened
        office_app_identifier_image = os.path.join(PARENT_DIR, "office_app_identifier.png")
        office_app_identifier_pos = pag.locateCenterOnScreen(
            office_app_identifier_image, minSearchTime=10, confidence=0.9, grayscale=True
        )

        time.sleep(4)
        # check_license_agreement()
        print("a")
        time.sleep(2)
        check_activation_wizard()

    except Exception as ex:
        app_logger.error(f"Error starting {app.capitalize()} app, Ex: {ex}")
        sys.exit(1)


def check_license_agreement():
    """
    Check if there is a license agreement dialog and accept it
    """
    try:
        check_license_image = os.path.join(PARENT_DIR, "accept_license_agreement.png")
        check_license_pos = pag.locateCenterOnScreen(check_license_image, minSearchTime=3)
        pag.click(check_license_pos)
    except Exception as ex:
        app_logger.error(f"Error writing into a word file, Ex: {ex}")
        sys.exit(1)


def check_activation_wizard():
    """
    Check if there is a activation wizard dialog and cancel it\n
    Prerequisites:
        - Opened Word
    """
    try:
        ms_activation_image = os.path.join(PARENT_DIR, "activation_wizard_identifier.png")
        ms_activation_pos = pag.locateCenterOnScreen(
            ms_activation_image, minSearchTime=3, confidence=0.8, grayscale=True
        )
        pag.click(ms_activation_pos)
        if ms_activation_pos:
            pag.press("c")

    except Exception as ex:
        app_logger.error(f"Error writing into a word file, Ex: {ex}")
        sys.exit(1)


def write_word_file(text):
    """
    Open new file, write the given text and save it\n
    Prerequisites:
        - Opened Word
    """
    try:
        pag.hotkey("ctrl", "n")
        time.sleep(0.5)
        pag.press("tab")
        time.sleep(0.5)
        pag.press("enter")
        time.sleep(2)
        pag.write(text, 0.1)
        pag.hotkey("alt", "f4")
        time.sleep(0.5)
        pag.press("n")
        time.sleep(0.5)

    except Exception as ex:
        app_logger.error(f"Error writing into a word file, Ex: {ex}")
        sys.exit(1)
