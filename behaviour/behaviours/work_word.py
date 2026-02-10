from app_config import automation_config
from app_logger import app_logger
from behaviour.behaviour import BaseBehaviour
from behaviour.models.behaviour import BehaviourCategory
from behaviour.scripts_pyautogui.office_utils import office_utils
from cleanup_manager import CleanupManager


class BehaviourWorkWord(BaseBehaviour):
    """
    Behaviour for working with Microsoft Word.
    NOTE: This behaviour is currently unfinished.
    """

    # Class-level metadata
    id = "work_word"
    display_name = "Work Word"
    category = BehaviourCategory.IDLE
    description = "Simulates work on Microsoft Word"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)

        if cleanup_manager is not None:
            self.user = automation_config["general"]["user"]
        else:
            self.user = None

    def _is_available(self) -> bool:
        return False
        # Only available on Windows
        return self.os_type == "Windows"

    def run_behaviour(self):
        app_logger.info("Starting work_word behaviour")

        self.cleanup_manager.add_cleanup_task(lambda: office_utils.close_app("word"))

        office_utils.start_app("word")

        app_logger.info("Completed work_word behaviour")
