"""
Utility functions for Linux and Windows operating systems
-
Prerequisites:
    - Windows or linux operating system
"""

import platform
import sys
import time
import os
import pyautogui as pag


from app_logger import app_logger

PARENT_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))

os_type = platform.system()


def open_terminal():
    """
    Open terminal\n
    """
    try:
        if os_type == "Linux":
            pag.press("win")
            time.sleep(1)
            pag.write("terminal", 0.1)
            time.sleep(2)
            pag.press("enter")
        else:
            pag.hotkey("win", "r")
            time.sleep(1)
            pag.write("cmd", 0.1)
            time.sleep(1)
            pag.press("enter")
    except Exception as ex:
        app_logger.error(f"Error opening terminal, Ex: {ex}")
        sys.exit(1)


def close_terminal():
    """
    Close terminal\n
    Prerequisites:
        - opened terminal
    """
    try:
        if os_type == "Linux":
            pag.hotkey("ctrl", "c")
            time.sleep(1)
            pag.hotkey("ctrl", "d")
        else:
            pag.write("exit", 0.1)
            pag.press("enter")

    except Exception as ex:
        app_logger.error(f"Error closing terminal, Ex: {ex}")
        sys.exit(1)


def write_file(filename, text):
    """
    Write text into file using nano or notepad\n
    """
    try:
        if os_type == "Linux":
            pag.write(f"nano {filename}", 0.1)
            pag.press("enter")
            time.sleep(1)
            pag.write(text, 0, 1)
            time.sleep(1)
            pag.hotkey("ctrl", "x")
            time.sleep(1)
            pag.press("y")
            time.sleep(1)
            pag.press("enter")
        else:
            pag.write(f"notepad {filename}", 0.1)
            pag.press("enter")
            time.sleep(1)
            pag.press("y")
            time.sleep(0.5)
            pag.hotkey("ctrl", "a")
            time.sleep(0.5)
            pag.hotkey("ctrl", "x")
            time.sleep(0.5)
            pag.write(text, 0.1)
            time.sleep(1)
            pag.hotkey("ctrl", "s")
            time.sleep(1)
            pag.hotkey("alt", "f4")

    except Exception as ex:
        app_logger.error(f"Error writing text into file, Ex: {ex}")
        sys.exit(1)


def delete_file(filename):
    """
    Force delete file\n
    """
    try:
        if os_type == "Linux":
            pag.write(f"sudo rm -f {filename}", 0.1)
        else:
            pag.write(f"del {filename}", 0.1)
        time.sleep(1)
        pag.press("enter")
    except Exception as ex:
        app_logger.error(f"Error deleting file {filename}, Ex: {ex}")


def compile_c_program(filename, output_filename):
    """
    Compile c program\n
    Prerequisites:
        - build-essential installed
        - c program in directory
    """
    try:
        pag.write(f"gcc {filename} -o {output_filename}", 0.1)
        time.sleep(1)
        pag.press("enter")
    except Exception as ex:
        app_logger.error(f"Error copiling c program, Ex: {ex}")
        sys.exit(1)


def run_c_program(filename):
    """
    Run compiled c program\n
    Prerequisites:
        - Linux os
        - compiled c program in directory
    """
    try:
        pag.write(f"./{filename}", 0.1)
        time.sleep(1)
        pag.press("enter")
    except Exception as ex:
        app_logger.error(f"Error running c program, Ex: {ex}")
        sys.exit(1)


def run_ps_program(filename):
    """
    Run powershell script\n
    Prerequisites:
        - Windows os
        - Powershell script in directory
    """
    try:
        pag.write(f"powershell -file {filename}", 0.1)
        time.sleep(1)
        pag.press("enter")
    except Exception as ex:
        app_logger.error(f"Error running powershell program, Ex: {ex}")


def escape():
    """
    Escape, ESC
    """
    pag.press("esc")


def copy():
    """
    Copy, CTRL+C
    """
    pag.hotkey("ctrl", "c")


def cut():
    """
    Cut, CTRL+X
    """
    pag.hotkey("ctrl", "x")


def open_downloads_folder():
    pag.hotkey("win", "r")
    time.sleep(0.1)
    pag.write("downloads", 0.1)
    time.sleep(0.1)
    pag.press("enter")


def paste():
    # TODO: add recognition of duplicate files
    pag.hotkey("ctrl", "v")


def rename(new_name):
    """
    Renames selected file\n
    Prerequisites:
        - File selected
    """
    time.sleep(1)
    pag.press("f2")
    time.sleep(1)
    pag.write(new_name, 0.1)
    time.sleep(1)
    pag.press("enter")
    time.sleep(1)


def maximize_window():
    """
    Maxizes window, WIN + UP\n
    Prerequisites:
        - Opened window
    """
    pag.hotkey("win", "up")


def minimize_window():
    """
    Maxizes window, WIN + DOWN\n
    Prerequisites:
        - Opened window
    """
    pag.hotkey("win", "down")


def altf4():
    """
    Quit, ALT + F4
    """
    pag.hotkey("alt", "f4")


def ctrlf():
    """
    Find, CTRL + F
    """
    pag.hotkey("ctrl", "f")


def open_file_options():
    """
    Open file options on windows, SHIFT + F10
    Prerequisites:
        - File selected
    """
    pag.hotkey("shift", "f10")


def extract_file():
    """
    Extract file on windows
    Prerequisites:
        - File selected
    """
    open_file_options()
    time.sleep(1)
    pag.press("t")
    time.sleep(1)
    pag.press("enter")
    time.sleep(1)
    pag.press("enter")
