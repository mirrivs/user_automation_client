import platform
import threading

from app_config import app_config
from behaviour.ids import BehaviourId
from behaviour.models import BehaviourCategory
from cleanup_manager import CleanupManager, CleanupTask
from lib.cancellable_futures import CancellableThreadPoolExecutor, OperationCancelled, _current_executor
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
