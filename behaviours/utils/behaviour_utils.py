import threading
import ctypes
from typing import Callable, Optional
from app_logger import app_logger


class BehaviourException(Exception):
    def __init__(self, msg: str, exception: Exception = None):
        log_message = msg
        if exception is not None:
            log_message += f", Original Exception: {exception}"

        app_logger.error(log_message)
        super().__init__(log_message)


class BehaviourThread(threading.Thread):
    """
    Base class for interruptible behaviour threads with automatic cleanup support.

    This thread can be instantly stopped using the stop() method, which raises
    SystemExit in the thread. The cleanup() method is always called in the finally
    block, ensuring resources are properly released.

    Usage:
        class MyBehaviour(BehaviourThread):
            def run_behaviour(self):
                # Your automation code here
                time.sleep(100)  # Can be interrupted

            def cleanup(self):
                # Cleanup code here
                super().cleanup()  # Call parent cleanup

        behaviour = MyBehaviour()
        behaviour.start()
        # Later...
        behaviour.stop()  # Instantly interrupts and runs cleanup
    """

    def __init__(self, cleanup_manager=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cleanup_manager = cleanup_manager
        self._cleanup_callbacks = []

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
        """
        Override this method with your behaviour automation code.
        This is where you put your actual automation logic.
        """
        raise NotImplementedError("Subclasses must implement run_behaviour()")

    def cleanup(self):
        """
        Override this method to add custom cleanup logic.
        Always call super().cleanup() at the end of your override.
        """
        app_logger.info(f"Running cleanup for {self.__class__.__name__}")

        # Execute registered cleanup callbacks in reverse order (LIFO)
        for callback in reversed(self._cleanup_callbacks):
            try:
                callback()
            except Exception as e:
                app_logger.error(f"Error in cleanup callback: {e}")

        # Run cleanup manager if provided
        if self.cleanup_manager:
            try:
                self.cleanup_manager.run_cleanup()
            except Exception as e:
                app_logger.error(f"Error in cleanup manager: {e}")

    def register_cleanup(self, callback: Callable):
        """
        Register a cleanup callback to be executed when thread stops.
        Callbacks are executed in reverse order (LIFO).

        Args:
            callback: A callable with no arguments to execute during cleanup
        """
        self._cleanup_callbacks.append(callback)

    def stop(self):
        """Instantly stop this thread by raising SystemExit"""
        if not self.is_alive():
            app_logger.warning(f"Cannot stop {self.__class__.__name__} - thread is not alive")
            return

        app_logger.info(f"Stopping {self.__class__.__name__}...")
        self._raise_exception(SystemExit)

    def _raise_exception(self, exctype):
        """
        Raise an exception in this thread.

        Args:
            exctype: The exception class to raise (e.g., SystemExit)
        """
        if not self.is_alive():
            return

        tid = self.ident
        if tid is None:
            app_logger.warning("Cannot raise exception - thread ID is None")
            return

        # Raise the exception in the target thread
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(tid),
            ctypes.py_object(exctype)
        )

        if res == 0:
            raise ValueError("Invalid thread id")
        elif res > 1:
            # Revert if something went wrong
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
            raise SystemError("PyThreadState_SetAsyncExc failed")


def get_behaviour_cfg(behaviour_name: str, config: dict) -> dict:
    """
    Retrieve behaviour configuration from main config
    """
    behaviour_cfg = config.get("behaviours", {}).get(behaviour_name, {})
    if not behaviour_cfg:
        raise BehaviourException(f"Configuration for behaviour '{behaviour_name}' not found")

    return behaviour_cfg