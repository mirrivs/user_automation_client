from app_config import automation_config
from behaviour.behaviour import WebEmailBehaviour
from behaviour.ids import BehaviourId
from behaviour.models import BehaviourCategory
from cleanup_manager import CleanupManager
from lib.selenium.models import EmailClient
from src.logger import app_logger


class BehaviourWorkOrganizationWeb(WebEmailBehaviour):
    id: BehaviourId = "work_organization_web"
    display_name = "Organization Web"
    category = BehaviourCategory.IDLE
    description = "Simulates browsing organization website"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)
        self.general_config = automation_config["general"]
        self.user = self.general_config["user"]
        self.email_client_type = EmailClient(self.general_config["email_client"])

    @classmethod
    def is_available(cls) -> bool:
        return cls.os_type in ["Windows"] and cls.landscape_id not in [8]

    def run_behaviour(self):
        app_logger.info(f"Starting {self.id} behaviour")

        self.setup_web_email_behaviour(self.user, self.email_client_type)

        self.pool.submit(self.browser.search_by_url, self.general_config["organization_web_url"]).result()
        self.pool.sleep(4)

        self.pool.submit(self.selenium_controller.browse_organization_website, 45).result()

        app_logger.info(f"Completed {self.id} behaviour")
