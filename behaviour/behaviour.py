import ctypes
import platform
import threading
from typing import Callable

from app_logger import app_logger
from behaviour.models.behaviour import BehaviourCategory
from cleanup_manager import CleanupManager


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

    def __init__(self, cleanup_manager: CleanupManager, *args, **kwargs):
        """
        Initialize the behaviour.

        Args:
            cleanup_manager: CleanupManager instance for resource cleanup.
        """
        super().__init__(*args, **kwargs)

        # Use class-level attributes, fallback to class name
        if self.id is None:
            self.id = self.__class__.__name__
        if self.display_name is None:
            self.display_name = self.id

        # Cleanup management
        self.cleanup_manager = cleanup_manager
        self._cleanup_callbacks = []

    @classmethod
    def is_available(cls) -> bool:
        """
        Override this method to check if the behaviour can run on this system.
        Default: always available.

        This is a class method so availability can be checked without instantiation.
        """
        return True

    def run(self):
        """Main thread execution - handles SystemExit and calls cleanup"""
        try:
            self.run_behaviour()
        except SystemExit:
            app_logger.info(f"{self.__class__.__name__} interrupted via SystemExit")
        except Exception as e:
            app_logger.error(f"Error in {self.__class__.__name__}: {e}", exc_info=True)
        finally:
            self.cleanup()

    def run_behaviour(self):
        """Override this method with your behaviour automation code."""
        raise NotImplementedError("Subclasses must implement run_behaviour()")

    def cleanup(self):
        """Override this method to add custom cleanup logic."""
        app_logger.info(f"Running cleanup for {self.__class__.__name__}")

        for callback in reversed(self._cleanup_callbacks):
            try:
                callback()
            except Exception as e:
                app_logger.error(f"Error in cleanup callback: {e}")

        if self.cleanup_manager:
            try:
                self.cleanup_manager.run_cleanup()
            except Exception as e:
                app_logger.error(f"Error in cleanup manager: {e}")

    def register_cleanup(self, callback: Callable):
        """Register a cleanup callback to be executed when thread stops."""
        self._cleanup_callbacks.append(callback)

    def stop(self):
        """Instantly stop this thread by raising SystemExit"""
        if not self.is_alive():
            app_logger.warning(f"Cannot stop {self.__class__.__name__} - thread is not alive")
            return

        app_logger.info(f"Stopping {self.__class__.__name__}...")
        self._raise_exception(SystemExit)

    def _raise_exception(self, exctype):
        """Raise an exception in this thread."""
        if not self.is_alive():
            return

        tid = self.ident
        if tid is None:
            app_logger.warning("Cannot raise exception - thread ID is None")
            return

        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))

        if res == 0:
            raise ValueError("Invalid thread id")
        elif res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def __repr__(self):
        available = self.is_available()
        return f"<{self.__class__.__name__}(id='{self.id}', available={available})>"
