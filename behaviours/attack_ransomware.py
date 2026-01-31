import platform
import time
import pyautogui as pag

from app_config import app_config
from app_logger import app_logger
from cleanup_manager import CleanupManager

from utils.selenium_utils import EdgeSeleniumController, EmailClientType, FirefoxSeleniumController
from utils.behaviour import BaseBehaviour, BehaviourCategory

from scripts_pyautogui.os_utils import os_utils
from scripts_pyautogui.browser_utils.browser_utils import BrowserUtils, EdgeUtils
from scripts_pyautogui.win_utils import win_utils

from selenium.webdriver.common.by import By


class BehaviourAttackRansomware(BaseBehaviour):
    """
    Behaviour for downloading and opening malicious email attachment.
    """

    # Class-level metadata
    id = "attack_ransomware"
    display_name = "Ransomware"
    category = BehaviourCategory.ATTACK
    description = "Ransomware attack - downloads and opens malicious email attachment"

    def __init__(self, cleanup_manager: CleanupManager = None):
        super().__init__(cleanup_manager)
        
        if cleanup_manager is not None:
            self.landscape_id = int(app_config["app"]["landscape"])
            self.user = app_config["behaviour"]["general"]["user"]
            self.behaviour_general = app_config["behaviour"]
            self.behaviour_cfg = app_config["behaviour"]["attack_ransomware"]
            self.email_client_type: EmailClientType = "owa" if self.landscape_id in [2] else "roundcube"
        else:
            self.landscape_id = None
            self.user = None
            self.behaviour_general = None
            self.behaviour_cfg = None
            self.email_client_type = None
            
        self.selenium_controller = None

    def _is_available(self) -> bool:
        return self.os_type in ["Windows", "Linux"]

    def run_behaviour(self):
        app_logger.info("Starting attack_ransomware behaviour")

        self.selenium_controller = (
            FirefoxSeleniumController()
            if self.os_type == "Linux"
            else EdgeSeleniumController()
        )

        self.cleanup_manager.selenium_controller = self.selenium_controller
        self.cleanup_manager.add_cleanup_task(self.selenium_controller.quit_driver)

        self.selenium_controller.maximize_driver_window()
        time.sleep(4)

        BrowserUtils.search_by_url(self.user["roundcube_url"])
        time.sleep(4)

        self.selenium_controller.email_client_login(self.user["email"], self.user["password"])

        if self.email_client_type == "roundcube":
            self.selenium_controller.roundcube_set_language()

        time.sleep(4)

        unread_emails = self.selenium_controller.get_unread_emails()

        for email in unread_emails:
            subject_link = None
            if self.email_client_type == "owa":
                subject_link = email.find_element(
                    By.XPATH, "//span[contains(@class, 'lvHighlightAllClass lvHighlightSubjectClass')]")
            else:
                subject_link = email.find_element(By.CSS_SELECTOR, "td.subject a")

            if subject_link.text == self.behaviour_cfg["malicious_email_subject"]:
                subject_link.click()
                break

        if self.email_client_type == "roundcube":
            iframe = self.selenium_controller.driver.find_element(By.NAME, "messagecontframe")
            time.sleep(1)
            self.selenium_controller.driver.switch_to.frame(iframe)
            downloaded_attachments = self.selenium_controller.email_client_download_email_attachments()

        if self.email_client_type == "owa":
            self.selenium_controller.owa_search_link_in_email()
            time.sleep(5)
            EdgeUtils.allow_suspicious_file()
            time.sleep(3)
            pag.press("tab")
            time.sleep(0.5)
            pag.press("enter")
            os_utils.extract_file()
        else:
            for attachment_name in downloaded_attachments:
                if self.os_type == "Linux":
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

        app_logger.info("Completed attack_ransomware behaviour")