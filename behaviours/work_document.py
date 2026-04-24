from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from app_config import automation_config
from behaviour import get_image_path
from behaviour.behaviour import WebEmailBehaviour
from behaviour.config import get_behaviour_cfg
from behaviour.ids import BehaviourId
from behaviour.models import BehaviourCategory
from cleanup_manager import CleanupManager
from lib.autogui.actions import os_utils
from lib.selenium.models import EmailClient
from src.logger import app_logger


class BehaviourWorkDocument(WebEmailBehaviour):
    """
    Behaviour for working with text document.
    NOTE: This behaviour is currently unfinished.
    """

    # Class-level metadata
    id: BehaviourId = "work_document"
    display_name = "Work Document"
    category = BehaviourCategory.IDLE
    description = "Simulates work with text document"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)

        self.general_cfg = automation_config["general"]
        self.user = self.general_cfg["user"]
        self.config = get_behaviour_cfg(self.id)
        self.email_client_type = EmailClient(self.general_cfg["email_client"])

    @classmethod
    def is_available(cls) -> bool:
        return cls.os_type == "Windows"

    def run_behaviour(self):
        app_logger.info(f"Starting {self.id} behaviour")

        if self.general_cfg["use_web_office_apps"]:
            self.web_behaviour()
        else:
            self.local_behaviour()

        app_logger.info(f"Completed {self.id} behaviour")

    def web_behaviour(self):
        self.setup_web_email_behaviour(self.user, self.email_client_type, force_external_credentials=True)

        self.pool.submit(self.browser.search_by_url, "https://word.cloud.microsoft/").result()

        self.pool.sleep(3)

        self.selenium_controller.wait(5).until(
            EC.presence_of_element_located((By.XPATH, "//button[text()='Sign in']"))
        ).click()

        self.pool.sleep(3)

        self.pool.submit(self.email_client.login).result()

        self.pool.sleep(3)

        self.selenium_controller.wait(5).until(
            EC.presence_of_element_located((By.XPATH, "//button[&data-testid='0300']"))
        ).click()

    def local_behaviour(self):
        try:
            app_logger.info("Attempting to open Microsoft Word")
            # self.cleanup_manager.add_cleanup_task(lambda: os_utils.close_app("word"))
            self.pool.submit(os_utils.start_app, "word", get_image_path("apps/ms_office/word/icon.png")).result()
            app_logger.info("Microsoft Word opened successfully")

        except TimeoutError:
            app_logger.warning("Word not found, falling back to LibreOffice Writer")
            # self.cleanup_manager.add_cleanup_task(lambda: os_utils.close_app("soffice"))
            self.pool.submit(
                os_utils.start_app,
                "libreoffice writer",
                get_image_path("apps/libre_office/writer/icon.png"),
                grayscale=True,
            ).result()
            app_logger.info("LibreOffice Writer opened successfully")
