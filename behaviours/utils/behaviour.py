from enum import Enum
import platform
import threading
import ctypes
from typing import Callable
from app_config import automation_config
from app_logger import app_logger


class BehaviourCategory(Enum):
    IDLE = "Idle"
    ATTACK = "Attack"


class BehaviourException(Exception):
    def __init__(self, msg: str, exception: Exception = None):
        log_message = msg
        if exception is not None:
            log_message += f", Original Exception: {exception}"

        app_logger.error(log_message)
        super().__init__(log_message)


class BaseBehaviour(threading.Thread):
    """
    Base class for interruptible behaviour threads with automatic cleanup support.

    Class attributes to override in subclasses:
        id: str - Unique identifier for the behaviour
        display_name: str - Human-readable name
        category: BehaviourCategory - Category (IDLE or ATTACK)
        description: str - Description of what the behaviour does

    Methods to override:
        _is_available() - Return True if behaviour can run on this system
        run_behaviour() - Main automation logic
        cleanup() - Cleanup logic (call super().cleanup() at end)
    """

    # Class-level metadata - override in subclasses
    id: str = None
    display_name: str = None
    category: BehaviourCategory = BehaviourCategory.IDLE
    description: str = ""

    def __init__(self, cleanup_manager=None, *args, **kwargs):
        """
        Initialize the behaviour.
        
        Args:
            cleanup_manager: Optional CleanupManager instance for resource cleanup.
                           Can be None when just checking availability.
        """
        super().__init__(*args, **kwargs)
        
        # Use class-level attributes, fallback to class name
        if self.id is None:
            self.id = self.__class__.__name__
        if self.display_name is None:
            self.display_name = self.id
        
        # Check availability
        self.os_type = platform.system()
        self.is_available = self._is_available()
        
        # Cleanup management
        self.cleanup_manager = cleanup_manager
        self._cleanup_callbacks = []

    def _is_available(self) -> bool:
        """
        Override this method to check if the behaviour can run on this system.
        Default: always available.
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

        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(tid), ctypes.py_object(exctype)
        )

        if res == 0:
            raise ValueError("Invalid thread id")
        elif res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def __repr__(self):
        return f"<{self.__class__.__name__}(id='{self.id}', available={self.is_available})>"


def get_behaviour_cfg(behaviour_id: str, required: bool = False) -> dict:
    """
    Retrieve behaviour configuration from main config.
    
    Args:
        behaviour_id: Id of the behaviour to get config for
        required: If True, raises BehaviourException when config not found
        
    Returns:
        Behaviour configuration dict, or empty dict if not found and not required
    """
    behaviour_cfg = automation_config.get("behaviours", {}).get(behaviour_id, {})
    if not behaviour_cfg and required:
        raise BehaviourException(f"Configuration for task '{behaviour_id}' not found")
    return behaviour_cfg
