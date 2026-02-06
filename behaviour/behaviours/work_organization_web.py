import time

from app_config import automation_config
from app_logger import app_logger
from behaviour.scripts_pyautogui.browser_utils.browser_utils import BrowserUtils
from cleanup_manager import CleanupManager

from behaviour.selenium.models.email_client import EmailClient
from behaviour.selenium.selenium_controller import EmailClientUser, getSeleniumController
from behaviour.behaviour import BaseBehaviour, BehaviourCategory


class BehaviourWorkOrganizationWeb(BaseBehaviour):
    """
    Behaviour for browsing organization website.
    """

    # Class-level metadata
    id = "work_organization_web"
    display_name = "Organization Web"
    category = BehaviourCategory.IDLE
    description = "Simulates browsing organization website"

    def __init__(self, cleanup_manager: CleanupManager = None):
        super().__init__(cleanup_manager)

        if cleanup_manager is not None:
            self.user = automation_config["general"]["user"]
            self.email_client_type = EmailClient(automation_config["general"]["email_client"])

            is_o365 = self.email_client_type == EmailClient.O365
            email_client_user: EmailClientUser = {
                "name": (self.user["o365_email"] if is_o365 else self.user["domain_email"]).split(".")[0],
                "email": self.user["o365_email"] if is_o365 else self.user["domain_email"],
                "password": self.user["o365_password"] if is_o365 else self.user["domain_password"],
            }

            self.selenium_controller = getSeleniumController(self.email_client_type, email_client_user)
        else:
            self.user = None
            self.behaviour_general = None

    def _is_available(self) -> bool:
        return self.os_type in ["Windows", "Linux", "Darwin"]

    def run_behaviour(self):
        app_logger.info("Starting work_organization_web behaviour")

        self.cleanup_manager.selenium_controller = self.selenium_controller
        self.cleanup_manager.add_cleanup_task(self.selenium_controller.quit_driver)

        self.selenium_controller.maximize_driver_window()
        time.sleep(4)

        BrowserUtils.search_by_url(self.behaviour_general["organization_web_url"])
        time.sleep(4)

        self.selenium_controller.browse_organization_website(45)

        app_logger.info("Completed work_organization_web behaviour")
