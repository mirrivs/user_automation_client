import platform
import random
import sys
import os
import time
import pyautogui as pag

from app_config import app_config
from app_logger import app_logger
from cleanup_manager import CleanupManager

# Scripts imports
from scripts_pyautogui.os_utils import os_utils

# Append to path for custom imports
BEHAVIOUR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BEHAVIOUR_DIR, "templates")

LINUX_FILE = os.path.join(TEMPLATES_DIR, "c_program.txt")
WINDOWS_FILE = os.path.join(TEMPLATES_DIR, "ps_program.txt")

def behaviour_work_developer(cleanup_manager: CleanupManager):
    """
    This behaviour generates or responds to predefined email conversation using Roundcube web client 
    """
    user = app_config["behaviour"]["general"]["user"]

    filename = random.choice(["super_complex_code", "hello_world", "iam_working"])

    os_type = platform.system()

    os_utils.open_terminal()
    cleanup_manager.add_cleanup_task(os_utils.close_terminal)

    time.sleep(2)

    file_content = "Placeholder text"

    if os_type == "Linux":
        with open(LINUX_FILE, "r", encoding="utf-8") as file:
            file_content = file.read()
    else:
        filename = f"{filename}.ps1"
        with open(WINDOWS_FILE, "r", encoding="utf-8") as file:
            file_content = file.read()

    os_utils.write_file(filename, file_content)
    
    cleanup_manager.add_cleanup_task(os_utils.delete_file, filename)
    
    time.sleep(1)

    if os_type == "Linux":
        os_utils.run_c_program(filename)
    else:
        os_utils.run_ps_program(filename)

    time.sleep(4)

    file_cleanup_task = cleanup_manager.pop_cleanup_task()
    file_cleanup_task['function'](*file_cleanup_task.get('args', ()), **file_cleanup_task.get('kwargs', {}))
    
    terminal_cleanup_task = cleanup_manager.pop_cleanup_task()
    terminal_cleanup_task['function'](*terminal_cleanup_task.get('args', ()), **terminal_cleanup_task.get('kwargs', {}))