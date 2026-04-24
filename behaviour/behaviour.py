import platform
import threading
from typing import Mapping

from app_config import app_config
from behaviour.ids import BehaviourId
from behaviour.models import BehaviourCategory
from cleanup_manager import CleanupManager, CleanupTask
from lib.autogui.actions.browser import Browser, Edge, Firefox
from lib.cancellable_futures import CancellableThreadPoolExecutor, OperationCancelled, _current_executor
from lib.selenium.email_web_client import BaseEmailWebClient
from lib.selenium.models import EmailClient, EmailClientUser
from lib.selenium.selenium_controller import SeleniumController, getSeleniumController
from lib.selenium.user import build_email_client_user
from src.logger import app_logger


class BaseBehaviour(threading.Thread):
    """
    Base class for interruptible behaviour threads with automatic cleanup support.

    Class attributes to override in subclasses:
        id: BehaviourId - Unique identifier for the behaviour
        display_name: str - Human-readable name
        category: BehaviourCategory - Category (IDLE or ATTACK)
        description: str - Description of what the behaviour does

    Methods to override:
        is_available() - Class method to check if behaviour can run on this system
        run_behaviour() - Main automation logic
        cleanup() - Cleanup logic (call super().cleanup() at end)
    """

    id: BehaviourId
    display_name: str = "BaseBehaviour"
    category: BehaviourCategory = BehaviourCategory.IDLE
    description: str = ""

    os_type: str = platform.system()
    landscape_id = app_config["app"]["landscape_id"]

    def __init__(self, cleanup_manager: CleanupManager, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cleanup_manager = cleanup_manager

        self._cancel_event = threading.Event()
        self.pool = CancellableThreadPoolExecutor(max_workers=1)
        self.pool._global_event = self._cancel_event

    @classmethod
    def is_available(cls) -> bool:
        return True

    @property
    def cancel_requested(self) -> bool:
        return self._cancel_event.is_set()

    def request_cancel(self) -> None:
        self._cancel_event.set()

    def run(self):
        _current_executor.set(self.pool)
        try:
            self.run_behaviour()
        except OperationCancelled:
            app_logger.info(f"{self.__class__.__name__} cancelled")
        except SystemExit:
            app_logger.info(f"{self.__class__.__name__} interrupted via SystemExit")
        except Exception as e:
            app_logger.error(f"Error in {self.__class__.__name__}: {e}", exc_info=True)
        finally:
            self.cleanup()

    def run_behaviour(self):
        raise NotImplementedError("Subclasses must implement run_behaviour()")

    def cleanup(self):
        app_logger.info(f"Running cleanup for {self.__class__.__name__}")

        try:
            self.pool.shutdown(wait=True)
        except Exception as e:
            app_logger.error(f"Error shutting down pool: {e}")

        if self.cleanup_manager:
            try:
                self.cleanup_manager.run_cleanup()
            except Exception as e:
                app_logger.error(f"Error in cleanup manager: {e}")

    def register_cleanup(self, callback, *args, label: str | None = None, **kwargs) -> CleanupTask:
        return self.cleanup_manager.add_cleanup_task(callback, *args, label=label, **kwargs)

    def stop(self, timeout: float = 10):
        app_logger.info(f"Stopping {self.__class__.__name__}...")
        self.request_cancel()
        self.join(timeout=timeout)

        if self.is_alive():
            app_logger.warning(f"{self.__class__.__name__} did not stop within {timeout}s")

    def __repr__(self):
        available = self.is_available()
        return f"<{self.__class__.__name__}(id='{self.id}', available={available})>"


class WebBehaviour(BaseBehaviour):
    """Base behaviour with shared web browser + selenium setup."""

    browser: Browser
    selenium_controller: SeleniumController

    def get_browser_client(self) -> Browser:
        return Firefox() if self.os_type == "Linux" else Edge()

    def setup_web_behaviour(self) -> Browser:
        self.browser = self.get_browser_client()
        return self.browser

    def setup_selenium(self, email_client_type: EmailClient, user: EmailClientUser, startup_sleep: float = 4) -> None:
        self.setup_web_behaviour()
        self.selenium_controller = getSeleniumController(email_client_type, user)

        self.cleanup_manager.selenium_controller = self.selenium_controller
        self.cleanup_manager.add_cleanup_task(self.selenium_controller.quit_driver)

        self.selenium_controller.maximize_driver_window()
        self.pool.sleep(startup_sleep)


class WebEmailBehaviour(WebBehaviour):
    """Base behaviour with shared web + email client initialization."""

    email_client: BaseEmailWebClient
    email_client_type: EmailClient
    email_client_user: EmailClientUser

    def setup_web_email_behaviour(
        self,
        user: Mapping[str, str],
        email_client_type: EmailClient,
        force_external_credentials: bool = False,
        startup_sleep: float = 4,
    ) -> None:
        self.email_client_type = email_client_type
        self.email_client_user = build_email_client_user(
            user,
            email_client_type,
            force_external_credentials=force_external_credentials,
        )
        self.setup_selenium(self.email_client_type, self.email_client_user, startup_sleep=startup_sleep)
        self.email_client = self.selenium_controller.email_client
