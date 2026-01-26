import sys
import os
import pyautogui as pag

#
# Unfinished
#

# Append to path for custom imports
BEHAVIOUR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BEHAVIOUR_DIR)

TOP_DIR = os.path.join(BEHAVIOUR_DIR, "..")
sys.path.append(TOP_DIR)

TEMPLATES_DIR = os.path.join(BEHAVIOUR_DIR, "templates")

# Custom imports
from app_config import app_config
from app_logger import app_logger
from cleanup_manager import CleanupManager
import config_handler as config_handler

# Utilities imports
from utils.behaviour_utils import BehaviourThread

# Scripts imports
from scripts_pyautogui.os_utils import os_utils
from scripts_pyautogui.office_utils import office_utils


class BehaviourWorkWord(BehaviourThread):
    """
    Behaviour for working with Microsoft Word.

    This class can be directly instantiated and started from the behaviour manager.
    NOTE: This behaviour is currently unfinished.
    """

    # Behaviour metadata
    name = "work_word"
    display_name = "Work Word"
    category = "IDLE"
    description = "Simulates work on Microsoft Word"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)
        self.user = app_config["behaviour"]["general"]["user"]

    def run_behaviour(self):
        """Main behaviour execution - can be interrupted at any time"""
        app_logger.info("Starting work_word behaviour")

        office_utils.start_app("word")

        app_logger.info("Completed work_word behaviour")

