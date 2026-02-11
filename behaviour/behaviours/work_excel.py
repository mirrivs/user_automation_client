import time

from app_config import automation_config
from app_logger import app_logger
from behaviour.behaviour import BaseBehaviour
from behaviour.behaviour_cfg import get_behaviour_cfg
from behaviour.models.behaviour import BehaviourCategory
from behaviour.scripts_pyautogui.browser_utils.browser_utils import BrowserUtils
from behaviour.scripts_pyautogui.office_utils import office_utils
from behaviour.selenium.email_web_client import EmailClientUser
from behaviour.selenium.models.email_client import EmailClient
from behaviour.selenium.selenium_controller import getSeleniumController
from cleanup_manager import CleanupManager


class BehaviourWorkExcel(BaseBehaviour):
    """
    Behaviour for working with Microsoft Word.
    NOTE: This behaviour is currently unfinished.
    """

    # Class-level metadata
    id = "work_excel"
    display_name = "Work Excel"
    category = BehaviourCategory.IDLE
    description = "Simulates work on Microsoft Excel"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)

        self.general_cfg = automation_config["general"]
        self.user = self.general_cfg["user"]
        self.behaviour_cfg = get_behaviour_cfg(self.id)
        self.email_client_type = EmailClient(self.general_cfg["email_client"])

    @classmethod
    def is_available(cls) -> bool:
        return cls.os_type == "Windows"

    def run_behaviour(self):
        app_logger.info(f"Starting {self.id} behaviour")

        if automation_config["general"]["enable_o365"]:
            self.web_behaviour()
        else:
            self.local_behaviour()

        app_logger.info(f"Completed {self.id} behaviour")

    def web_behaviour(self):
        is_o365 = self.email_client_type == EmailClient.O365
        email_client_user: EmailClientUser = {
            "name": (self.user["o365_email"] if is_o365 else self.user["domain_email"]).split(".")[0],
            "email": self.user["o365_email"] if is_o365 else self.user["domain_email"],
            "password": self.user["o365_password"] if is_o365 else self.user["domain_password"],
        }

        self.selenium_controller = getSeleniumController(self.email_client_type, email_client_user)

        email_client = self.selenium_controller.email_client

        self.cleanup_manager.selenium_controller = self.selenium_controller
        self.cleanup_manager.add_cleanup_task(self.selenium_controller.quit_driver)

        self.selenium_controller.maximize_driver_window()
        time.sleep(4)

        BrowserUtils.search_by_url("https://excel.cloud.microsoft/")

        email_client.login()

    def local_behaviour(self):
        self.cleanup_manager.add_cleanup_task(lambda: office_utils.close_app("word"))
        office_utils.start_app("word")
