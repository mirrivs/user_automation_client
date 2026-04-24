import platform

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from app_config import app_config, automation_config
from behaviour.behaviour import WebEmailBehaviour
from behaviour.config import get_behaviour_cfg
from behaviour.ids import BehaviourId
from behaviour.models import BehaviourCategory
from behaviour.models.config import AttackPhishingCfg
from cleanup_manager import CleanupManager
from lib.selenium.models import EmailClient
from src.logger import app_logger


class BehaviourAttackPhishing(WebEmailBehaviour):
    """
    Behaviour for opening phishing website from email.
    """

    # Class-level metadata
    id: BehaviourId = "attack_phishing"
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
        self.config = get_behaviour_cfg(self.id, AttackPhishingCfg, True)

        self.setup_web_email_behaviour(self.user, self.email_client_type)

        self.pool.submit(self.browser.search_by_url, self.general_cfg["organization_mail_server_url"]).result()

        self.pool.submit(self.email_client.login).result()

        if self.email_client.type == EmailClient.ROUNDCUBE:
            self.pool.submit(self.selenium_controller.roundcube_set_language).result()

        self.pool.sleep(4)

        unread_emails = self.pool.submit(self.email_client.get_unread_emails).result()

        for email in unread_emails:
            if self.email_client.type == EmailClient.ROUNDCUBE:
                subject_link = email.find_element(By.CSS_SELECTOR, "td.subject a")
            else:
                subject_link = email.find_element(
                    By.XPATH, "//span[contains(@class, 'lvHighlightAllClass lvHighlightSubjectClass')]"
                )
            if subject_link.text == self.config["malicious_email_subject"]:
                subject_link.click()
                break

        if self.email_client.type == EmailClient.ROUNDCUBE:
            iframe = self.selenium_controller.driver.find_element(By.NAME, "messagecontframe")
            self.pool.sleep(1)
            self.selenium_controller.driver.switch_to.frame(iframe)

        self.pool.submit(self.email_client.email_allow_files).result()
        found_phishing_link = False

        try:
            self.selenium_controller.driver.find_element(
                By.XPATH, "//a[contains(text(), 'SECURE ACCOUNT') or contains(text(), 'ZABEZPEČIŤ ÚČET')]"
            ).click()

            if self.email_client.type == EmailClient.ROUNDCUBE:
                self.selenium_controller.driver.switch_to.default_content()
            found_phishing_link = True
            self.pool.sleep(2)

            self.selenium_controller.switch_tab()
            self.pool.submit(
                self.selenium_controller.phishing_enter_credentials,
                self.user["internal_email"],
                self.user["internal_password"],
            ).result()
            self.pool.sleep(1)
            self.pool.submit(self.browser.close_latest_tab).result()

            app_logger.info("Entered phishing credentials")
        except NoSuchElementException:
            pass

        if found_phishing_link:
            self.selenium_controller.switch_tab()
        else:
            app_logger.error("No phishing link found")
            raise RuntimeError("No phishing link found")

        app_logger.info(f"Completed {self.id} behaviour")
