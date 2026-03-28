import os
import platform
import random

from app_config import automation_config
from behaviour.behaviour import BaseBehaviour
from behaviour.ids import BehaviourId
from behaviour.models import BehaviourCategory
from behaviours.consts import TEMPLATES_DIR
from cleanup_manager import CleanupManager
from lib.autogui.actions import os_utils
from src.logger import app_logger

LINUX_FILE = os.path.join(TEMPLATES_DIR, "c_program.txt")
WINDOWS_FILE = os.path.join(TEMPLATES_DIR, "ps_program.txt")


class BehaviourWorkDeveloper(BaseBehaviour):
    """
    Behaviour for simulating developer work by writing and running code.
    """

    id: BehaviourId = "work_developer"
    display_name = "Developer Work"
    category = BehaviourCategory.IDLE
    description = "Simulates developer activities"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)
        self.os_type = platform.system()

        if cleanup_manager is not None:
            self.user = automation_config["general"]["user"]
            self.filename = random.choice(["super_complex_code", "hello_world", "iam_working"])
        else:
            self.user = None
            self.filename = None

    @classmethod
    def is_available(cls) -> bool:
        return False
        # cls.os_type in ["Windows"]

    def run_behaviour(self):
        app_logger.info("Starting work_developer behaviour")

        self.pool.submit(os_utils.open_terminal).result()
        terminal_cleanup = self.cleanup_manager.add_cleanup_task(os_utils.close_terminal, label="close_terminal")

        self.pool.sleep(2)

        file_content = "Placeholder text"

        if self.os_type == "Linux":
            with open(LINUX_FILE, "r", encoding="utf-8") as file:
                file_content = file.read()
        else:
            self.filename = f"{self.filename}.ps1"
            with open(WINDOWS_FILE, "r", encoding="utf-8") as file:
                file_content = file.read()

        self.pool.submit(os_utils.write_file, self.filename, file_content).result()
        file_cleanup = self.cleanup_manager.add_cleanup_task(
            os_utils.delete_file,
            self.filename,
            label="delete_temp_file",
        )

        self.pool.sleep(1)

        if self.os_type == "Linux":
            self.pool.submit(os_utils.run_c_program, self.filename).result()
        else:
            self.pool.submit(os_utils.run_ps_program, self.filename).result()

        self.pool.sleep(4)

        self.cleanup_manager.run_task(file_cleanup)
        self.cleanup_manager.run_task(terminal_cleanup)

        app_logger.info("Completed work_developer behaviour")
