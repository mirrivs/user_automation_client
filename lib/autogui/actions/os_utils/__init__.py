"""
Utility functions for Linux and Windows operating systems
-
Prerequisites:
    - Windows or linux operating system
"""

import os
import platform
import sys

import pyautogui as pag
from exceptions import OperationCancelled

from lib.autogui import write
from lib.cancellable_futures import sleep
from src.logger import app_logger

PARENT_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))

os_type = platform.system()


def open_terminal():
    """
    Open terminal\n
    """
    try:
        if os_type == "Linux":
            pag.press("win")
            sleep(1)
            write("terminal", 0.1)
            sleep(2)
            pag.press("enter")
        else:
            pag.hotkey("win", "r")
            sleep(1)
            write("cmd", 0.1)
            sleep(1)
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
            sleep(1)
            pag.hotkey("ctrl", "d")
        else:
            write("exit", 0.1)
            pag.press("enter")
    except OperationCancelled:
        raise
    except Exception as ex:
        app_logger.error(f"Error closing terminal, Ex: {ex}")


def write_file(filename, text):
    """
    Write text into file using nano or notepad\n
    """
    try:
        if os_type == "Linux":
            write(f"nano {filename}", 0.1)
            pag.press("enter")
            sleep(1)
            write(text, 0)
            sleep(1)
            pag.hotkey("ctrl", "x")
            sleep(1)
            pag.press("y")
            sleep(1)
            pag.press("enter")
        else:
            write(f"notepad {filename}", 0.1)
            pag.press("enter")
            sleep(1)
            pag.press("y")
            sleep(0.5)
            pag.hotkey("ctrl", "a")
            sleep(0.5)
            pag.hotkey("ctrl", "x")
            sleep(0.5)
            write(text, 0.1)
            sleep(1)
            pag.hotkey("ctrl", "s")
            sleep(1)
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
            write(f"sudo rm -f {filename}", 0.1)
        else:
            write(f"del {filename}", 0.1)
        sleep(1)
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
        write(f"gcc {filename} -o {output_filename}", 0.1)
        sleep(1)
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
        write(f"./{filename}", 0.1)
        sleep(1)
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
        write(f"powershell -file {filename}", 0.1)
        sleep(1)
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
    sleep(0.1)
    write("downloads", 0.1)
    sleep(0.1)
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
    sleep(1)
    pag.press("f2")
    sleep(1)
    write(new_name, 0.1)
    sleep(1)
    pag.press("enter")
    sleep(1)


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
    sleep(1)
    pag.press("t")
    sleep(1)
    pag.press("enter")
    sleep(1)
    pag.press("enter")
