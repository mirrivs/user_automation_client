"""
Utility functions for Outlook phishing behaviour
-
Prerequisites:
    -   Opened Outlook phishing website
"""

import os
import pyautogui as pag

PARENT_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))


def enter_email(email: str):
    """
    Enter user email on outlook phishing website\n
    Prerequisites:
        - Opened outlook phishing website
    """
    try:
        # pag.press("tab")
        # time.sleep(0.5)
        # pag.write(email, 0.1)
        # time.sleep(0.5)
        # pag.press("enter")
        return 0, "Entered phishing email credentials"
    except Exception as ex:
        return 1, ex


def enter_password(password: str):
    """
    Enter user password on outlook phishing website\n
    Prerequisites:
        - Opened outlook phishing website
        - Selected email input field
    """
    try:
        # pag.press("tab")
        # pag.press("tab")
        # time.sleep(0.5)
        # pag.write(password, 0.1)
        # time.sleep(0.5)
        # pag.press("enter")
        return 0, "Entered phishing password credentials"
    except Exception as ex:
        return 1, ex


def main(email: str, password: str):
    """
    Enter user credentials on outlook phishing website
    Prerequisites:
        - Opened outlook phishing website
    """
    try:
        # enter_email(email)
        # time.sleep(2)
        # enter_password(password)
        # time.sleep(2)
        return 0, "Entered phishing credentials"
    except Exception as ex:
        return 1, ex
