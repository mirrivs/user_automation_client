"""
Utility functions for MS office on Windows
-
Prerequisites:
    - Windows operating system
    - MS Office installed
"""

import os
import sys

import pyautogui as pag

from lib.autogui import locate_image_center
from lib.cancellable_futures import sleep
from src.logger import app_logger

PARENT_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))


def start_app(app: str):
    """
    Open app\n
    """
    try:
        pag.press("win")
        sleep(0.5)
        pag.write(app, 0.1)

        image = None
        app_image_mapping = {
            "word": "explorer_word.png",
            "excel": "explorer_excel.png",
            "powerpoint": "explorer_powerpoint.png",
        }
        image = os.path.join(PARENT_DIR, app_image_mapping.get(app, ""))

        if image:
            app_image = locate_image_center(image, minSearchTime=5, confidence=0.8, grayscale=True)
            pag.click(app_image)
            pag.press("enter")
        else:
            raise ValueError("Invalid app name.")

        # Wait for office app identifier to be displayed - app is opened
        office_app_identifier_image = os.path.join(PARENT_DIR, "office_app_identifier.png")
        office_app_identifier_pos = locate_image_center(
            office_app_identifier_image, minSearchTime=10, confidence=0.9, grayscale=True
        )

        sleep(4)
        sleep(2)
        check_activation_wizard()

    except Exception as ex:
        app_logger.error(f"Error starting {app.capitalize()} app, Ex: {ex}")
        sys.exit(1)


def close_app(app: str):
    print("Closing the app")


def check_license_agreement():
    """
    Check if there is a license agreement dialog and accept it
    """
    try:
        check_license_image = os.path.join(PARENT_DIR, "accept_license_agreement.png")
        check_license_pos = locate_image_center(check_license_image, minSearchTime=3)
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
        ms_activation_pos = locate_image_center(ms_activation_image, minSearchTime=3, confidence=0.8, grayscale=True)
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
        sleep(0.5)
        pag.press("tab")
        sleep(0.5)
        pag.press("enter")
        sleep(2)
        pag.write(text, 0.1)
        pag.hotkey("alt", "f4")
        sleep(0.5)
        pag.press("n")
        sleep(0.5)

    except Exception as ex:
        app_logger.error(f"Error writing into a word file, Ex: {ex}")
        sys.exit(1)
