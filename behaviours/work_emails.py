import platform
import time

from app_config import app_config
from app_logger import app_logger
from cleanup_manager import CleanupManager

# Utilities imports
from utils.selenium_utils import EdgeSeleniumController, FirefoxSeleniumController, EmailClientType, getSeleniumController
from utils.email_manager import EmailManager
from utils.behaviour_utils import get_behaviour_cfg, BehaviourThread

# Scripts imports
from scripts_pyautogui.browser_utils.browser_utils import BrowserUtils

# Selenium imports
from selenium.webdriver.common.by import By


class BehaviourWorkEmails(BehaviourThread):
    """
    Behaviour for generating or responding to predefined email conversations using Roundcube/OWA web client.

    This class can be directly instantiated and started from the behaviour manager.
    """

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)
        self.landscape_id = int(app_config["app"]["landscape"])
        self.user = app_config["behaviour"]["general"]["user"]
        self.behaviour_general = app_config["behaviour"]["general"]
        self.behaviour_cfg = get_behaviour_cfg("work_emails", app_config)
        self.email_manager = EmailManager()
        self.selenium_controller = None

    def run_behaviour(self):
        """Main behaviour execution - can be interrupted at any time"""
        app_logger.info("Starting work_emails behaviour")

        self.selenium_controller = getSeleniumController("owa" if self.landscape_id in [2] else "roundcube")
        email_client = self.selenium_controller.email_client

        # Register selenium controller with cleanup manager
        self.cleanup_manager.selenium_controller = self.selenium_controller
        self.cleanup_manager.add_cleanup_task(self.selenium_controller.quit_driver)

        self.selenium_controller.maximize_driver_window()
        time.sleep(4)

        BrowserUtils.search_by_url(self.behaviour_general["organization_mail_server_url"])

        email_client.login(self.user["email"], self.user["password"])

        if email_client.type == "roundcube":
            self.selenium_controller.roundcube_set_language()

        time.sleep(4)

        unread_emails = email_client.get_unread_emails()

        responded = False
        # Read and reply to received emails from email conversations
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

                # Reply to email if a valid response is available
                reply = self.email_manager.get_email_response(email_id)
                if reply is not None:
                    sender_name = self.user["email"].split(".")[0].capitalize()
                    email_client.reply_to_email(sender_name, reply["subject"], reply["email_body"])
                    responded = True

                else:
                    time.sleep(5)

        # Start new email conversation
        if not responded and self.behaviour_general.get("is_conversation_starter", False):
            email = self.email_manager.get_email_starter()
            sender_name = self.user["email"].split(".")[0].capitalize()
            email_client.send_email(
                sender_name, self.behaviour_cfg["email_receivers"], email["subject"], email["email_body"])

        app_logger.info("Completed work_emails behaviour")


# Legacy function wrapper for backward compatibility
def behaviour_work_emails(cleanup_manager: CleanupManager):
    """
    Legacy function wrapper - creates and runs the behaviour class.
    """
    behaviour = BehaviourWorkEmails(cleanup_manager)
    behaviour.start()
    behaviour.join()
