"""
Utility functions for Office365 phishing
-
Prerequisites:
    - Opened office365 phishing website
"""

import os
import sys
import pyautogui as pag
import time

from app_logger import app_logger

PARENT_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))


def enter_email(email: str):
    """
    Enter user email on office365 phishing website\n
    Prerequisites:
        - Opened office365 email phishing website
    """
    try:
        pag.press("tab")
        time.sleep(0.5)
        pag.write(email, 0.1)
        time.sleep(0.5)
        pag.press("enter")
    except Exception as ex:
        app_logger.error(f"Error entering email on office365 phishing website, Ex: {ex}")
        sys.exit(1)


def enter_password(password: str):
    """
    Enter user password on office365 phishing website\n
    Prerequisites:
        - Opened office365 password phishing website
    """
    try:
        pag.press("tab")
        pag.press("tab")
        time.sleep(0.5)
        pag.write(password, 0.1)
        time.sleep(0.5)
        pag.press("enter")
    except Exception as ex:
        app_logger.error(f"Error entering password on office365 phishing website, Ex: {ex}")
        sys.exit(1)


def main(email: str, password: str):
    """
    Enter user credentials on office365 phishing website
    Prerequisites:
        - Opened office365 phishing website
    """
    try:
        enter_email(email)
        time.sleep(2)
        enter_password(password)
        time.sleep(2)
    except Exception as ex:
        app_logger.error(f"Error entering user credentials on office365 phishing website, Ex: {ex}")
        sys.exit(1)
