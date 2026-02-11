import platform
import sys
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from app_config import app_config, automation_config
from app_logger import app_logger
from behaviour.behaviour import BaseBehaviour
from behaviour.behaviour_cfg import get_behaviour_cfg
from behaviour.models.behaviour import BehaviourCategory
from behaviour.models.behaviour_cfg import AttackPhishingCfg
from behaviour.scripts_pyautogui.browser_utils.browser_utils import BrowserUtils
from behaviour.selenium.email_web_client import EmailClientUser
from behaviour.selenium.models.email_client import EmailClient
from behaviour.selenium.selenium_controller import getSeleniumController
from cleanup_manager import CleanupManager


class BehaviourAttackPhishing(BaseBehaviour):
    """
    Behaviour for opening phishing website from email.
    """

    # Class-level metadata
    id = "attack_phishing"
    display_name = "Phishing"
    category = BehaviourCategory.ATTACK
    description = "Attack phishing behaviour - opens phishing website from email"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)

        self.general_cfg = app_config["automation"]["general"]
        self.user = self.general_cfg["user"]
        self.email_client_type = EmailClient(automation_config["general"]["email_client"])

    @classmethod
    def is_available(cls) -> bool:
        return False
        return platform.system() in ["Windows", "Linux", "Darwin"]

    def run_behaviour(self):
        app_logger.info(f"Starting {self.id} behaviour")
        self.behaviour_cfg = get_behaviour_cfg(self.id, AttackPhishingCfg, True)

        is_o365 = self.email_client_type == EmailClient.O365
        email_client_user: EmailClientUser = {
            "name": (self.user["o365_email"] if is_o365 else self.user["domain_email"]).split(".")[0],
            "email": self.user["o365_email"] if is_o365 else self.user["domain_email"],
            "password": self.user["o365_password"] if is_o365 else self.user["domain_password"],
        }

        self.selenium_controller = getSeleniumController(self.email_client_type, email_client_user)
        self.email_client = self.selenium_controller.email_client

        self.cleanup_manager.selenium_controller = self.selenium_controller
        self.cleanup_manager.add_cleanup_task(self.selenium_controller.quit_driver)

        self.selenium_controller.maximize_driver_window()
        time.sleep(4)

        BrowserUtils.search_by_url(self.general_cfg["organization_mail_server_url"])

        self.email_client.login()

        if self.email_client.type == EmailClient.ROUNDCUBE:
            self.selenium_controller.roundcube_set_language()

        time.sleep(4)

        unread_emails = self.email_client.get_unread_emails()

        for email in unread_emails:
            if self.email_client.type == EmailClient.ROUNDCUBE:
                subject_link = email.find_element(By.CSS_SELECTOR, "td.subject a")
            else:
                subject_link = email.find_element(
                    By.XPATH, "//span[contains(@class, 'lvHighlightAllClass lvHighlightSubjectClass')]"
                )
            if subject_link.text == self.behaviour_cfg["malicious_email_subject"]:
                subject_link.click()
                break

        if self.email_client.type == EmailClient.ROUNDCUBE:
            iframe = self.selenium_controller.driver.find_element(By.NAME, "messagecontframe")
            time.sleep(1)
            self.selenium_controller.driver.switch_to.frame(iframe)

        self.email_client.email_allow_files()
        found_phishing_link = False

        try:
            self.selenium_controller.driver.find_element(
                By.XPATH, "//a[contains(text(), 'SECURE ACCOUNT') or contains(text(), 'ZABEZPEČIŤ ÚČET')]"
            ).click()

            if self.email_client.type == EmailClient.ROUNDCUBE:
                self.selenium_controller.driver.switch_to.default_content()
            found_phishing_link = True
            time.sleep(2)

            self.selenium_controller.switch_tab()
            self.selenium_controller.phishing_enter_credentials(self.user["domain_email"], self.user["domain_password"])
            time.sleep(1)
            BrowserUtils.close_latest_tab()

            app_logger.info("Entered phishing credentials")
        except NoSuchElementException:
            pass

        if found_phishing_link:
            self.selenium_controller.switch_tab()
        else:
            app_logger.error("No phishing link found")
            sys.exit(1)

        app_logger.info(f"Completed {self.id} behaviour")
