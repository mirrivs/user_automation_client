import pyautogui as pag
from selenium.webdriver.common.by import By

from app_config import automation_config
from behaviour.behaviour import BaseBehaviour
from behaviour.config import get_behaviour_cfg
from behaviour.ids import BehaviourId
from behaviour.models import BehaviourCategory
from behaviour.models.config import AttackReverseShellCfg
from cleanup_manager import CleanupManager
from lib.autogui.actions.browser import Edge, Firefox
from lib.autogui.actions.win_utils import win_utils
from lib.selenium.models import EmailClient
from lib.selenium.selenium_controller import (
    EmailClientUser,
    getSeleniumController,
)
from src.logger import app_logger


class BehaviourAttackReverseShell(BaseBehaviour):
    """
    Behaviour for downloading and opening malicious reverse shell attachment from email.
    """

    # Class-level metadata
    id: BehaviourId = "attack_reverse_shell"
    display_name = "Reverse Shell"
    category = BehaviourCategory.ATTACK
    description = "Reverse shell attack - downloads and opens malicious attachment from email"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)

        self.user = automation_config["general"]["user"]
        self.config: AttackReverseShellCfg = get_behaviour_cfg(self.id, AttackReverseShellCfg, True)

    @classmethod
    def is_available(cls) -> bool:
        return False
        return cls.os_type in ["Windows", "Linux"]

    def run_behaviour(self):
        app_logger.info(f"Starting {self.id} behaviour")

        browser = Firefox() if self.os_type == "Linux" else Edge()

        self.email_client_type = EmailClient(automation_config["general"]["email_client"])

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

        self.pool.submit(browser.search_by_url, automation_config["general"]["organization_mail_server_url"]).result()
        self.pool.sleep(4)

        self.pool.submit(self.selenium_controller.email_client.login).result()

        if self.email_client_type == "roundcube":
            self.pool.submit(self.selenium_controller.roundcube_set_language).result()

        self.pool.sleep(4)

        unread_emails = self.pool.submit(self.selenium_controller.email_client.get_unread_emails).result()

        for email in unread_emails:
            subject_link = None
            if self.email_client_type == "owa":
                subject_link = email.find_element(
                    By.XPATH,
                    "//span[contains(@class, 'lvHighlightAllClass lvHighlightSubjectClass')]",
                )
            else:
                subject_link = email.find_element(By.CSS_SELECTOR, "td.subject a")

            if subject_link.text == self.config["malicious_email_subject"]:
                subject_link.click()
                break

        if self.email_client_type == EmailClient.OWA:
            iframe = self.selenium_controller.driver.find_element(By.NAME, "messagecontframe")
            self.pool.sleep(1)
            self.selenium_controller.driver.switch_to.frame(iframe)

        downloaded_attachments = self.pool.submit(
            self.selenium_controller.email_client_download_email_attachments
        ).result()

        for attachment_name in downloaded_attachments:
            if self.os_type == "Linux":
                print("linux behaviour")
            else:
                self.pool.submit(win_utils.open_downloads_folder).result()
                self.pool.sleep(1)
                self.pool.submit(win_utils.ctrlf).result()
                self.pool.sleep(0.5)
                pag.write(attachment_name.split(".")[0], 0.1)
                self.pool.sleep(0.5)
                pag.press("enter")
                self.pool.sleep(2)
                pag.press("tab")
                self.pool.sleep(0.5)
                pag.press("tab")
                self.pool.sleep(0.5)
                pag.hotkey("ctrl", "space")
                self.pool.sleep(0.5)
                pag.hotkey("alt", "enter")
                self.pool.sleep(0.5)
                pag.press("k")
                self.pool.sleep(0.5)
                pag.press("a")
                self.pool.sleep(0.5)
                pag.press("enter")
                self.pool.sleep(0.5)
                pag.press("enter")

        app_logger.info("Completed attack_reverse_shell behaviour")

