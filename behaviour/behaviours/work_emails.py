import platform
import time

from app_config import automation_config
from app_logger import app_logger
from behaviour.behaviour import BaseBehaviour, BehaviourCategory
from behaviour.behaviour_cfg import get_behaviour_cfg
from behaviour.scripts_pyautogui.browser_utils.browser_utils import BrowserUtils
from behaviour.selenium.email_web_client import EmailClientUser
from behaviour.selenium.models.email_client import EmailClient
from behaviour.selenium.selenium_controller import getSeleniumController
from cleanup_manager import CleanupManager
from email_manager.email_manager import EmailManager


class BehaviourWorkEmails(BaseBehaviour):
    """
    Behaviour for generating or responding to predefined email conversations.
    """

    # Class-level metadata
    id = "work_emails"
    display_name = "Work Emails"
    category = BehaviourCategory.IDLE
    description = "Generates or responds to predefined email conversations"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)

        self.general_cfg = automation_config["general"]
        self.user = self.general_cfg["user"]
        self.behaviour_cfg = get_behaviour_cfg("work_emails")
        self.email_client_type = EmailClient(self.general_cfg["email_client"])

    def _is_available(self) -> bool:
        return platform.system() in ["Windows", "Linux", "Darwin"]

    def run_behaviour(self):
        app_logger.info("Starting work_emails behaviour")

        self.email_manager = EmailManager()
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

        BrowserUtils.search_by_url(self.general_cfg["organization_mail_server_url"])

        email_client.login()

        if email_client.type == EmailClient.ROUNDCUBE:
            self.selenium_controller.roundcube_set_language()

        # Wait for the web to fully load
        time.sleep(6)

        unread_emails = email_client.get_unread_emails()

        responded_count = email_client.reply_to_emails(unread_emails)

        if not responded_count and self.general_cfg.get("is_conversation_starter", False):
            email_receivers = self.behaviour_cfg.get("email_receivers")
            if not email_receivers:
                app_logger.warning(
                    "Cannot start email conversation: 'email_receivers' not configured in behaviours.work_emails"
                )
                return

            email = self.email_manager.get_email_starter()
            email_client.send_email(email_receivers, email["subject"], email["email_body"])

        app_logger.info("Completed work_emails behaviour")
