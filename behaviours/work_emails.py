import platform

from app_config import automation_config
from behaviour.behaviour import WebEmailBehaviour
from behaviour.config import get_behaviour_cfg
from behaviour.ids import BehaviourId
from behaviour.models import BehaviourCategory
from behaviour.models.config import WorkEmailsCfg
from cleanup_manager import CleanupManager
from lib.email_manager.email_manager import EmailManager
from lib.selenium.models import EmailClient
from src.logger import app_logger


class BehaviourWorkEmails(WebEmailBehaviour):
    """
    Behaviour for generating or responding to predefined email conversations.
    """

    # Class-level metadata
    id: BehaviourId = "work_emails"
    display_name = "Work Emails"
    category = BehaviourCategory.IDLE
    description = "Generates or responds to predefined email conversations"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)

        self.general_cfg = automation_config["general"]
        self.user = self.general_cfg["user"]
        self.config = get_behaviour_cfg(self.id, WorkEmailsCfg)
        self.email_client_type = EmailClient(self.general_cfg["email_client"])

    @classmethod
    def is_available(cls) -> bool:
        return platform.system() in ["Windows", "Linux", "Darwin"]

    def run_behaviour(self):
        app_logger.info("Starting work_emails behaviour")

        self.email_manager = EmailManager()
        self.setup_web_email_behaviour(self.user, self.email_client_type)

        self.pool.submit(self.browser.search_by_url, self.general_cfg["organization_mail_server_url"]).result()

        self.pool.submit(self.email_client.login).result()

        if self.email_client.type == EmailClient.ROUNDCUBE:
            self.pool.submit(self.selenium_controller.roundcube_set_language).result()

        # Wait for the web to fully load
        self.pool.sleep(6)

        unread_emails = self.pool.submit(self.email_client.get_unread_emails).result()

        responded_count = self.pool.submit(self.email_client.reply_to_emails, unread_emails).result()

        if not responded_count and self.config.get("is_conversation_starter", False):
            email_receivers = self.config.get("email_receivers")
            if not email_receivers:
                app_logger.warning(
                    "Cannot start email conversation: 'email_receivers' not configured in behaviours.work_emails"
                )
                return

            email = self.email_manager.get_email_starter()
            self.pool.submit(
                self.email_client.send_email,
                email_receivers,
                email["subject"],
                email["email_body"],
            ).result()

        app_logger.info("Completed work_emails behaviour")
