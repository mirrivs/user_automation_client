import platform
import time
import sys

from app_config import app_config
from app_logger import app_logger
from cleanup_manager import CleanupManager

from utils.selenium_utils import getSeleniumController
from utils.behaviour import get_behaviour_cfg, BaseBehaviour, BehaviourCategory

from scripts_pyautogui.browser_utils.browser_utils import BrowserUtils

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


class BehaviourAttackPhishing(BaseBehaviour):
    """
    Behaviour for opening phishing website from email.
    """

    # Class-level metadata
    id = "attack_phishing"
    display_name = "Phishing"
    category = BehaviourCategory.ATTACK
    description = "Attack phishing behaviour - opens phishing website from email"

    def __init__(self, cleanup_manager: CleanupManager = None):
        super().__init__(cleanup_manager)
        
        if cleanup_manager is not None:
            self.general_cfg = app_config["automation"]["general"]
            self.mail_client = self.general_cfg["mail_client"]
            self.user = self.general_cfg["user"]
            # Config is REQUIRED for attack_phishing - needs malicious_email_subject
            self.behaviour_cfg = get_behaviour_cfg("attack_phishing", app_config, required=True)
        else:
            self.general_cfg = None
            self.mail_client = None
            self.user = None
            self.behaviour_cfg = None
            
        self.selenium_controller = None

    def _is_available(self) -> bool:
        return platform.system() in ["Windows", "Linux", "Darwin"]

    def run_behaviour(self):
        app_logger.info("Starting attack_phishing behaviour")

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

        for email in unread_emails:
            if email_client.type == "roundcube":
                subject_link = email.find_element(By.CSS_SELECTOR, "td.subject a")
            else:
                subject_link = email.find_element(
                    By.XPATH, "//span[contains(@class, 'lvHighlightAllClass lvHighlightSubjectClass')]")
            if subject_link.text == self.behaviour_cfg["malicious_email_subject"]:
                subject_link.click()
                break

        if email_client.type == "roundcube":
            iframe = self.selenium_controller.driver.find_element(By.NAME, "messagecontframe")
            time.sleep(1)
            self.selenium_controller.driver.switch_to.frame(iframe)

        email_client.email_allow_files()
        found_phishing_link = False
        
        try:
            self.selenium_controller.driver.find_element(
                By.XPATH, "//a[contains(text(), 'SECURE ACCOUNT') or contains(text(), 'ZABEZPEČIŤ ÚČET')]").click()

            if email_client.type == "roundcube":
                self.selenium_controller.driver.switch_to.default_content()
            found_phishing_link = True
            time.sleep(2)

            self.selenium_controller.switch_tab()
            self.selenium_controller.phishing_roundcube_enter_credentials(self.user["email"], self.user["password"])
            time.sleep(1)
            BrowserUtils.close_latest_tab()

            app_logger.info("Entered roundcube phishing credentials")
        except NoSuchElementException:
            pass

        try:
            self.selenium_controller.driver.find_element(
                By.XPATH, "//a[contains(text(), 'Verify Password') or contains(text(), 'Overiť heslo')]").click()

            if email_client.type == "roundcube":
                self.selenium_controller.driver.switch_to.default_content()

            found_phishing_link = True
            time.sleep(2)

            self.selenium_controller.switch_tab()
            self.selenium_controller.phishing_owa_enter_credentials(self.user["email"], self.user["password"])
            time.sleep(1)
            BrowserUtils.close_latest_tab()

            app_logger.info("Entered owa phishing credentials")
        except NoSuchElementException:
            pass

        if found_phishing_link:
            self.selenium_controller.switch_tab()
        else:
            app_logger.error("No phishing link found")
            sys.exit(1)

        app_logger.info("Completed attack_phishing behaviour")