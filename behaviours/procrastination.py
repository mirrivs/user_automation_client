import random
from datetime import datetime

from app_config import automation_config
from behaviour.behaviour import WebEmailBehaviour
from behaviour.config import get_behaviour_cfg
from behaviour.ids import BehaviourId
from behaviour.models import BehaviourCategory
from behaviour.models.config import ProcrastinationCfg
from cleanup_manager import CleanupManager
from lib.cancellable_futures import CancellableThreadPoolExecutor
from lib.general.random_choice import weighted_random_choice
from lib.selenium.models import EmailClient
from src.logger import app_logger


class BehaviourProcrastination(WebEmailBehaviour):
    """
    Behaviour for procrastinating on scrolling kitten images or watching YouTube shorts.
    """

    # Class-level metadata
    id: BehaviourId = "procrastination"
    display_name = "Procrastination"
    category = BehaviourCategory.IDLE
    description = "Simulates procrastination activities like browsing"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)

        # Replace the default single-worker pool with one sized for this behaviour
        self.pool = CancellableThreadPoolExecutor(max_workers=10)
        self.pool._global_event = self._cancel_event

        self.user = automation_config["general"]["user"]
        self.config = get_behaviour_cfg(self.id, ProcrastinationCfg)
        self.email_client_type = EmailClient(automation_config["general"]["email_client"])

    @classmethod
    def is_available(cls) -> bool:
        return cls.os_type in ["Windows", "Linux", "Darwin"]

    def run_behaviour(self):
        app_logger.info(f"Starting {self.id} behaviour")

        self.setup_web_email_behaviour(self.user, self.email_client_type, startup_sleep=3)

        test_time = random.uniform(self.config["min_duration"], self.config["max_duration"])
        start_time = datetime.now()

        selected_preference = weighted_random_choice(self.config["preference"])
        app_logger.info(f"Selected preference: {selected_preference}")

        if selected_preference == "youtube":
            self.pool.submit(self.browser.search_by_url, "youtube.com").result()
            self.pool.sleep(3)

            watch_duration = test_time - (datetime.now() - start_time).total_seconds()
            self.pool.submit(
                self.selenium_controller.procrastinate_watch_youtube_shorts,
                watch_duration,
            ).result()

        elif selected_preference == "kittens":
            self.pool.submit(self.browser.search_by_url, "kittens").result()
            self.pool.sleep(3)

            if self.os_type == "Linux":
                self.pool.submit(self.selenium_controller.accept_google_cookies).result()
                self.pool.sleep(2)

            scroll_duration = test_time - (datetime.now() - start_time).total_seconds()
            self.pool.submit(
                self.selenium_controller.procrastinate_scroll_images,
                round(scroll_duration),
            ).result()

        else:
            app_logger.warning(f"Unknown test preference: {selected_preference}")

        app_logger.info(f"Completed {self.id} behaviour")
