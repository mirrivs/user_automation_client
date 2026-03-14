import platform
import threading
from typing import Callable

from app_config import app_config
from behaviour.models.behaviour import BehaviourCategory
from cleanup_manager import CleanupManager
from lib.cancellable_futures import CancellableThreadPoolExecutor, OperationCancelled, _current_executor
from src.logger import app_logger


class BaseBehaviour(threading.Thread):
    """
    Base class for interruptible behaviour threads with automatic cleanup support.

    Class attributes to override in subclasses:
        id: str - Unique identifier for the behaviour
        display_name: str - Human-readable name
        category: BehaviourCategory - Category (IDLE or ATTACK)
        description: str - Description of what the behaviour does

    Methods to override:
        is_available() - Class method to check if behaviour can run on this system
        run_behaviour() - Main automation logic
        cleanup() - Cleanup logic (call super().cleanup() at end)
    """

    # Class-level metadata - override in subclasses
    id: str = "base"
    display_name: str = "BaseBehaviour"
    category: BehaviourCategory = BehaviourCategory.IDLE
    description: str = ""

    # Store system info
    os_type: str = platform.system()
    landscape_id = app_config["app"]["landscape_id"]

    def __init__(self, cleanup_manager: CleanupManager, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.id is None:
            self.id = self.__class__.__name__
        if self.display_name is None:
            self.display_name = self.id

        self.cleanup_manager = cleanup_manager
        self._cleanup_callbacks = []
        self.pool = CancellableThreadPoolExecutor(max_workers=1)

    @classmethod
    def is_available(cls) -> bool:
        return True

    def run(self):
        """Main thread execution - runs behaviour, cleans up."""
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

        for callback in reversed(self._cleanup_callbacks):
            try:
                callback()
            except Exception as e:
                app_logger.error(f"Error in cleanup callback: {e}")

        try:
            self.pool.shutdown(wait=True)
        except Exception as e:
            app_logger.error(f"Error shutting down pool: {e}")

        if self.cleanup_manager:
            try:
                self.cleanup_manager.run_cleanup()
            except Exception as e:
                app_logger.error(f"Error in cleanup manager: {e}")

    def register_cleanup(self, callback: Callable):
        self._cleanup_callbacks.append(callback)

    def stop(self, timeout: float = 2):
        """Stop all pool tasks and wait for the behaviour thread to finish."""
        app_logger.info(f"Stopping {self.__class__.__name__}...")
        self.pool.cancel()
        self.join(timeout=timeout)

    def __repr__(self):
        available = self.is_available()
        return f"<{self.__class__.__name__}(id='{self.id}', available={available})>"
