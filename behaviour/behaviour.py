import platform
import threading
from typing import Callable

from app_config import app_config
from behaviour.models import BehaviourCategory
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
        self._cleanup_callbacks: list[Callable] = []

        # Cooperative cancellation: one event shared between the behaviour
        # thread and every pool task. Setting it triggers OperationCancelled
        # in any call to check() or sleep().
        self._cancel_event = threading.Event()
        self.pool = CancellableThreadPoolExecutor(max_workers=1)
        self.pool._global_event = self._cancel_event

    @classmethod
    def is_available(cls) -> bool:
        return True

    @property
    def cancel_requested(self) -> bool:
        """True if this behaviour has been asked to stop."""
        return self._cancel_event.is_set()

    def request_cancel(self) -> None:
        """Signal the behaviour and all its pool tasks to stop cooperatively."""
        self._cancel_event.set()

    def run(self):
        """Main thread execution - runs behaviour, cleans up."""
        # Bind the pool to this thread so module-level sleep()/check() work
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

    def stop(self, timeout: float = 10):
        """Request cancellation and wait for the behaviour thread to finish.

        This is the primary way the BehaviourManager terminates a running
        behaviour. The flow is:
          1. Set the shared cancel event → pool.check()/sleep() raise
             OperationCancelled in whichever task is running.
          2. join() waits for run() to finish (including cleanup).
        """
        app_logger.info(f"Stopping {self.__class__.__name__}...")
        self.request_cancel()
        self.join(timeout=timeout)

        if self.is_alive():
            app_logger.warning(f"{self.__class__.__name__} did not stop within {timeout}s")

    def __repr__(self):
        available = self.is_available()
        return f"<{self.__class__.__name__}(id='{self.id}', available={available})>"
