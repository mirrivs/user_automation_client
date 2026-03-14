from abc import ABC, abstractmethod

import pyautogui

from lib.cancellable_futures import sleep


class Browser(ABC):
    def search_by_url(self, url: str):
        pyautogui.hotkey("alt", "d")
        sleep(1)
        pyautogui.write(url, 0.1)
        pyautogui.press("enter")

    def open_new_tab(self):
        pyautogui.hotkey("ctrl", "t")

    def close_latest_tab(self):
        pyautogui.hotkey("ctrl", "w")

    @abstractmethod
    def close_all_tabs(self):
        """Each browser handles this differently"""
        ...

    @abstractmethod
    def search_by_text(self, text: str): ...


class Edge(Browser):
    def close_all_tabs(self):
        pyautogui.hotkey("ctrl", "shift", "w")

    def search_by_text(self, text: str):
        pyautogui.hotkey("ctrl", "e")
        sleep(1)
        pyautogui.write(text, 0.1)
        pyautogui.press("enter")


class Firefox(Browser):
    def close_all_tabs(self):
        pyautogui.hotkey("ctrl", "shift", "w")
        sleep(0.5)
        pyautogui.press("enter")  # firefox needs confirmation

    def search_by_text(self, text: str):
        pyautogui.hotkey("ctrl", "k")  # firefox uses ctrl+k
        sleep(1)
        pyautogui.write(text, 0.1)
        pyautogui.press("enter")
