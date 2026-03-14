import pyautogui

from behaviour.behaviour import BaseBehaviour
from behaviour.models.behaviour import BehaviourCategory
from behaviour.scripts_pyautogui.win_utils.win_utils import open_explorer
from cleanup_manager import CleanupManager
from src.logger import app_logger


class BehaviourTest(BaseBehaviour):
    id = "test"
    display_name = "Test"
    category = BehaviourCategory.IDLE
    description = "Test behaviour for explorer detection"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)

    @classmethod
    def is_available(cls) -> bool:
        return cls.os_type in ["Windows", "Linux", "Darwin"]

    def run_behaviour(self):
        app_logger.info(f"Starting {self.id} behaviour")

        pyautogui.click(open_explorer())
        app_logger.info(f"Completed {self.id} behaviour")
