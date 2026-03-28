from app_config import automation_config
from behaviour.behaviour import BaseBehaviour
from behaviour.ids import BehaviourId
from behaviour.models import BehaviourCategory
from cleanup_manager import CleanupManager
from lib.autogui.actions.browser import Edge, Firefox
from lib.selenium.email_web_client import EmailClientUser
from lib.selenium.models import EmailClient
from lib.selenium.selenium_controller import getSeleniumController
from src.logger import app_logger


class BehaviourWorkOrganizationWeb(BaseBehaviour):
    id: BehaviourId = "work_organization_web"
    display_name = "Organization Web"
    category = BehaviourCategory.IDLE
    description = "Simulates browsing organization website"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)
        self.general_config = automation_config["general"]
        self.user = self.general_config["user"]
        self.email_client_type = EmailClient(self.general_config["email_client"])

    @classmethod
    def is_available(cls) -> bool:
        return cls.os_type in ["Windows"] and cls.landscape_id not in [8]

    def run_behaviour(self):
        app_logger.info(f"Starting {self.id} behaviour")

        browser = Firefox() if self.os_type == "Linux" else Edge()

        is_o365 = self.email_client_type == EmailClient.O365
        email_client_user: EmailClientUser = {
            "name": (self.user["external_email"] if is_o365 else self.user["internal_email"]).split(".")[0],
            "email": self.user["external_email"] if is_o365 else self.user["internal_email"],
            "password": self.user["external_password"] if is_o365 else self.user["internal_password"],
        }
        self.selenium_controller = getSeleniumController(self.email_client_type, email_client_user)

        self.cleanup_manager.selenium_controller = self.selenium_controller
        self.cleanup_manager.add_cleanup_task(self.selenium_controller.quit_driver)

        self.selenium_controller.maximize_driver_window()
        self.pool.sleep(4)

        self.pool.submit(browser.search_by_url, self.general_config["organization_web_url"]).result()
        self.pool.sleep(4)

        self.pool.submit(self.selenium_controller.browse_organization_website, 45).result()

        app_logger.info(f"Completed {self.id} behaviour")

