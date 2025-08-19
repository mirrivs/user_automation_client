import platform
import time

from app_config import app_config
from utils.app_logger import app_logger
from cleanup_manager import CleanupManager

# Utilities imports
from utils.selenium_utils import EdgeSeleniumController, FirefoxSeleniumController, EmailClientType
from utils.email_manager import EmailManager

# Scripts imports
from scripts_pyautogui.browser_utils.browser_utils import BrowserUtils

# Selenium imports
from selenium.webdriver.common.by import By


def behaviour_work_emails(cleanup_manager: CleanupManager):
    """
    This behaviour generates or responds to predefined email conversation using Roundcube web client 
    """
    landscape_id = int(app_config["app"]["landscape"])

    user = app_config["behaviour"]["general"]["user"]
    behaviour_general = app_config["behaviour"]["general"]
    behaviour_cfg = app_config["behaviour"]["behaviours"]["work_emails"]

    email_client: EmailClientType = "owa" if landscape_id in [2] else "roundcube"

    os_type = platform.system()
    email_manager = EmailManager()

    selenium_controller = FirefoxSeleniumController(email_client) if os_type == "Linux" else EdgeSeleniumController(email_client)
    cleanup_manager.selenium_controller = selenium_controller

    selenium_controller.maximize_driver_window()
    time.sleep(4)

    BrowserUtils.search_by_url(behaviour_general["organization_mail_server_url"])

    selenium_controller.email_client_login(user["email"], user["password"])

    if email_client == "roundcube":
        selenium_controller.roundcube_set_language()

    time.sleep(4)

    unread_emails = selenium_controller.get_unread_emails()

    responded = False
    # Read and reply to received emails from email conversations
    for email in unread_emails:
        subject_link = None
        if landscape_id == 2:
            subject_link = email.find_element(
                By.XPATH, "//span[contains(@class, 'lvHighlightAllClass lvHighlightSubjectClass')]")
        else:
            subject_link = email.find_element(By.CSS_SELECTOR, "td.subject a")

        email_id = email_manager.get_email_id_by_subject(subject_link.text)
        if email_id:
            if landscape_id == 2:
                subject_link.click()
            else:
                email.click()

            unread_emails = selenium_controller.get_unread_emails()

            time.sleep(2)

            # Reply to email if a valid response is available
            reply = email_manager.get_email_response(email_id)
            if reply is not None:
                sender_name = user["email"].split(".")[0].capitalize()
                selenium_controller.reply_to_email(sender_name, reply["subject"], reply["email_body"])
                responded = True

            else:
                time.sleep(5)

    # Start new email conversation
    if not responded and behaviour_general.get("is_conversation_starter", False):
        email = email_manager.get_email_starter()
        sender_name = user["email"].split(".")[0].capitalize()
        selenium_controller.roundcube_write_email(
            sender_name, behaviour_cfg["email_receivers"], email["subject"], email["email_body"])
