import atexit
import os
import platform
import signal
import time
import sys
import pyautogui as pag

from cleanup_manager import CleanupManager

# Append to path for custom imports
behaviour_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(behaviour_dir)

top_dir = os.path.join(behaviour_dir, "..")
sys.path.append(top_dir)

# Custom imports
from app_config import app_config
from utils.app_logger import app_logger

# Utilities imports
from utils.selenium_utils import (
    EdgeSeleniumController,
    EmailClientType,
    FirefoxSeleniumController,
)

# Scripts imports
from scripts_pyautogui.win_utils import win_utils
from scripts_pyautogui.browser_utils.browser_utils import BrowserUtils

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By


def behaviour_attack_reverse_shell(cleanup_manager: CleanupManager):
    """
    This behaviour downloads a attachment in specific email and opens it
    """
    os_type = platform.system()

    # Read config
    config_file = os.path.join(top_dir, "config.yml")

    landscape_id = int(app_config["app"]["landscape"])

    behaviour_cfg = app_config["behaviour"]
    user = behaviour_cfg["general"]["user"]
    attack_reverse_shell_cfg = behaviour_cfg["attack_reverse_shell"]

    email_client: EmailClientType = "owa" if landscape_id in [2] else "roundcube"

    selenium_controller = (
        FirefoxSeleniumController() if os_type == "Linux" else EdgeSeleniumController()
    )
    cleanup_manager.selenium_controller = selenium_controller

    selenium_controller.maximize_driver_window()

    time.sleep(4)

    BrowserUtils.search_by_url(behaviour_cfg["general"]["organization_mail_server_url"])

    time.sleep(4)

    selenium_controller.email_client_login(user["email"], user["password"])

    if email_client == "roundcube":
        selenium_controller.roundcube_set_language()

    time.sleep(4)

    unread_emails = selenium_controller.get_unread_emails()

    # Read and reply to received emails from email conversations
    for email in unread_emails:
        subject_link = None
        if email_client == "owa":
            subject_link = email.find_element(
                By.XPATH,
                "//span[contains(@class, 'lvHighlightAllClass lvHighlightSubjectClass')]",
            )
        else:
            subject_link = email.find_element(By.CSS_SELECTOR, "td.subject a")

        if subject_link.text == attack_reverse_shell_cfg["malicious_email_subject"]:
            subject_link.click()
            break

    if email_client == "roundcube":
        iframe = selenium_controller.driver.find_element(By.NAME, "messagecontframe")
        time.sleep(1)
        selenium_controller.driver.switch_to.frame(iframe)

    downloaded_attachments = (
        selenium_controller.email_client_download_email_attachments()
    )

    for attachment_name in downloaded_attachments:
        if os_type == "Linux":
            print("linux behaviour")
        else:
            win_utils.open_downloads_folder()
            time.sleep(1)
            win_utils.ctrlf()
            time.sleep(0.5)
            pag.write(attachment_name.split(".")[0], 0.1)
            time.sleep(0.5)
            pag.press("enter")
            time.sleep(2)
            pag.press("tab")
            time.sleep(0.5)
            pag.press("tab")
            time.sleep(0.5)
            pag.hotkey("ctrl", "space")
            time.sleep(0.5)
            pag.hotkey("alt", "enter")
            time.sleep(0.5)
            pag.press("k")
            time.sleep(0.5)
            pag.press("a")
            time.sleep(0.5)
            pag.press("enter")
            time.sleep(0.5)
            pag.press("enter")
