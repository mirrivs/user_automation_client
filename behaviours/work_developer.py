import platform
import random
import sys
import os
import time
import pyautogui as pag

from app_config import app_config
from app_logger import app_logger
from cleanup_manager import CleanupManager

# Utilities imports
from utils.behaviour_utils import BehaviourThread

# Scripts imports
from scripts_pyautogui.os_utils import os_utils

# Append to path for custom imports
BEHAVIOUR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BEHAVIOUR_DIR, "templates")

LINUX_FILE = os.path.join(TEMPLATES_DIR, "c_program.txt")
WINDOWS_FILE = os.path.join(TEMPLATES_DIR, "ps_program.txt")


class BehaviourWorkDeveloper(BehaviourThread):
    """
    Behaviour for simulating developer work by writing and running code.

    This class can be directly instantiated and started from the behaviour manager.
    """

    # Behaviour metadata
    name = "work_developer"
    display_name = "Developer Work"
    category = "IDLE"
    description = "Simulates developer activities"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)
        self.user = app_config["behaviour"]["general"]["user"]
        self.os_type = platform.system()
        self.filename = random.choice(["super_complex_code", "hello_world", "iam_working"])

    def run_behaviour(self):
        """Main behaviour execution - can be interrupted at any time"""
        app_logger.info("Starting work_developer behaviour")

        os_utils.open_terminal()
        self.cleanup_manager.add_cleanup_task(os_utils.close_terminal)

        time.sleep(2)

        file_content = "Placeholder text"

        if self.os_type == "Linux":
            with open(LINUX_FILE, "r", encoding="utf-8") as file:
                file_content = file.read()
        else:
            self.filename = f"{self.filename}.ps1"
            with open(WINDOWS_FILE, "r", encoding="utf-8") as file:
                file_content = file.read()

        os_utils.write_file(self.filename, file_content)

        self.cleanup_manager.add_cleanup_task(os_utils.delete_file, self.filename)

        time.sleep(1)

        if self.os_type == "Linux":
            os_utils.run_c_program(self.filename)
        else:
            os_utils.run_ps_program(self.filename)

        time.sleep(4)

        file_cleanup_task = self.cleanup_manager.pop_cleanup_task()
        file_cleanup_task['function'](*file_cleanup_task.get('args', ()), **file_cleanup_task.get('kwargs', {}))

        terminal_cleanup_task = self.cleanup_manager.pop_cleanup_task()
        terminal_cleanup_task['function'](*terminal_cleanup_task.get('args', ()), **terminal_cleanup_task.get('kwargs', {}))

        app_logger.info("Completed work_developer behaviour")
