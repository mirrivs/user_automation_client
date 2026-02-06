"""
Utility functions for Web browsers browser
"""

import os
import sys
import pyautogui as pag
import time

from app_logger import app_logger

PARENT_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))


class BrowserUtils:
    @staticmethod
    def search_by_url(url: str):
        """
        Search in browser by url\n
        Prerequisites:
            - Opened browser
        """
        try:
            pag.hotkey("alt", "d")
            time.sleep(1)
            pag.write(url, 0.1)
            pag.press("enter")
        except Exception as ex:
            app_logger.error(f"Error searching url '{url}' in browser, Ex: {ex}")
            sys.exit(1)

    @staticmethod
    def open_new_tab():
        """
        Open new tab using shortcut\n
        Prerequisites:
            - Opened browser
        """
        try:
            pag.hotkey("ctrl", "t")
        except Exception as ex:
            app_logger.error(f"Error opening new tab in browser, Ex: {ex}")
            sys.exit(1)

    @staticmethod
    def close_latest_tab():
        """
        Close latest tab using shortcut\n
        Prerequisites:
            - Opened browser
        """
        try:
            pag.hotkey("ctrl", "w")
        except Exception as ex:
            app_logger.error(f"Error closing latest tab in browser, Ex: {ex}")
            sys.exit(1)


class EdgeUtils(BrowserUtils):
    @staticmethod
    def close_all_tabs():
        """
        Close all tabs using shortcut\n
        Prerequisites:
            - Opened edge
        """
        try:
            pag.hotkey("ctrl", "shift", "w")
        except Exception as ex:
            app_logger.error(f"Error closing all tabs in browser, Ex: {ex}")
            sys.exit(1)

    @staticmethod
    def search_by_text(text: str):
        """
        Search in browser by text\n
        Prerequisites:
            - Opened edge
        """
        try:
            pag.hotkey("ctrl", "e")
            time.sleep(1)
            pag.write(text, 0.1)
            pag.press("enter")
        except Exception as ex:
            app_logger.error(f"Error searching text '{text}' in browser, Ex: {ex}")
            sys.exit(1)

    @staticmethod
    def allow_suspicious_file():
        """
        Allow download of a suspicious file\n
        Prerequisites:
            - Opened edge
            - Attempted downloading suspicious file
        """
        try:
            pag.hotkey("ctrl", "j")
            time.sleep(1)
            pag.hotkey("shift", "tab")
            time.sleep(0.5)
            pag.hotkey("shift", "tab")
            time.sleep(0.5)
            pag.press("enter")
            time.sleep(2)
            pag.press("tab")
            time.sleep(0.5)
            pag.press("tab")
            time.sleep(0.5)
            pag.press("tab")
            time.sleep(0.5)
            pag.press("tab")
            time.sleep(0.5)
            pag.press("tab")
            time.sleep(0.5)
            pag.press("tab")
            time.sleep(0.5)
            pag.press("enter")
            time.sleep(1)
            pag.press("tab")
            time.sleep(0.5)
            pag.press("enter")
        except Exception as ex:
            app_logger.error(f"Error allowing download of a in browser, Ex: {ex}")
            sys.exit(1)


class FirefoxUtils(BrowserUtils):
    @staticmethod
    def close_all_tabs():
        """
        Close all tabs using shortcut\n
        Prerequisites:
            - Opened firefox
        """
        try:
            pag.hotkey("ctrl", "shift", "w")
            time.sleep(0.5)
            pag.press("enter")
        except Exception as ex:
            app_logger.error(f"Error closing all tabs in browser, Ex: {ex}")
            sys.exit(1)
