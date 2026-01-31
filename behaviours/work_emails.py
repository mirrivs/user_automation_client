import platform
import time

from app_config import app_config
from app_logger import app_logger
from cleanup_manager import CleanupManager

from utils.selenium_utils import getSeleniumController
from utils.email_manager import EmailManager
from utils.behaviour import get_behaviour_cfg, BaseBehaviour, BehaviourCategory

from scripts_pyautogui.browser_utils.browser_utils import BrowserUtils

from selenium.webdriver.common.by import By


class BehaviourWorkEmails(BaseBehaviour):
    """
    Behaviour for generating or responding to predefined email conversations.
    """

    # Class-level metadata
    id = "work_emails"
    display_name = "Work Emails"
    category = BehaviourCategory.IDLE
    description = "Generates or responds to predefined email conversations"

    def __init__(self, cleanup_manager: CleanupManager = None):
        super().__init__(cleanup_manager)
        
        if cleanup_manager is not None:
            self.general_cfg = app_config["automation"]["general"]
            self.mail_client = self.general_cfg["mail_client"]
            self.user = self.general_cfg["user"]
            # Config is optional for work_emails - uses general config
            self.behaviour_cfg = get_behaviour_cfg("work_emails", app_config)
            self.email_manager = EmailManager()
        else:
            self.general_cfg = None
            self.mail_client = None
            self.user = None
            self.behaviour_cfg = None
            self.email_manager = None
            
        self.selenium_controller = None

    def _is_available(self) -> bool:
        return platform.system() in ["Windows", "Linux", "Darwin"]

    def run_behaviour(self):
        app_logger.info("Starting work_emails behaviour")

        self.selenium_controller = getSeleniumController(self.mail_client)
        email_client = self.selenium_controller.email_client

        self.cleanup_manager.selenium_controller = self.selenium_controller
        self.cleanup_manager.add_cleanup_task(self.selenium_controller.quit_driver)

        self.selenium_controller.maximize_driver_window()
        time.sleep(4)

        BrowserUtils.search_by_url(self.general_cfg["organization_mail_server_url"])

        email_client.login(self.user["email"], self.user["password"])

        if email_client.type == "roundcube":
            self.selenium_controller.roundcube_set_language()

        time.sleep(4)

        unread_emails = email_client.get_unread_emails()

        responded = False
        for email in unread_emails:
            subject_link = None
            if email_client.type == "outlook":
                subject_link = email.find_element(
                    By.XPATH, "//span[contains(@class, 'lvHighlightAllClass lvHighlightSubjectClass')]")
            else:
                subject_link = email.find_element(By.CSS_SELECTOR, "td.subject a")

            email_id = self.email_manager.get_email_id_by_subject(subject_link.text)
            if email_id:
                if email_client.type == "outlook":
                    subject_link.click()
                else:
                    email.click()

                time.sleep(2)

                reply = self.email_manager.get_email_response(email_id)
                if reply is not None:
                    sender_name = self.user["email"].split(".")[0].capitalize()
                    email_client.reply_to_email(sender_name, reply["subject"], reply["email_body"])
                    responded = True
                else:
                    time.sleep(5)

        if not responded and self.general_cfg.get("is_conversation_starter", False):
            email_receivers = self.behaviour_cfg.get("email_receivers")
            if not email_receivers:
                app_logger.warning("Cannot start email conversation: 'email_receivers' not configured in tasks.work_emails")
                return
            
            email = self.email_manager.get_email_starter()
            sender_name = self.user["email"].split(".")[0].capitalize()
            email_client.send_email(
                sender_name, email_receivers, email["subject"], email["email_body"])

        app_logger.info("Completed work_emails behaviour")