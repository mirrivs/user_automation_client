from behaviours.utils.selenium_utils import (
    EdgeSeleniumController,
    FirefoxSeleniumController,
)
from typing import Callable, Dict, List, Any, Optional, Union


class CleanupManager:
    def __init__(self):
        self.selenium_controller: Optional[
            Union[EdgeSeleniumController, FirefoxSeleniumController]
        ] = None
        self.cleanup_stack: List[Dict[str, Any]] = []

    def add_cleanup_task(self, func: Callable, *args, **kwargs) -> int:
        """
        Add a cleanup task to the stack.

        Args:
            func: The function to call during cleanup
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            int: The index of the added task for later reference
        """
        task_index = len(self.cleanup_stack)
        self.cleanup_stack.append({"function": func, "args": args, "kwargs": kwargs})
        return task_index

    def pop_cleanup_task(self, index: Optional[int] = None) -> Dict[str, Any]:
        """
        Remove and return a cleanup task from the stack.

        Args:
            index: The index of the task to pop. If None, pops the last added task (LIFO).

        Returns:
            Dict[str, Any]: The cleanup task that was popped

        Raises:
            IndexError: If the stack is empty or index is out of range
        """
        if not self.cleanup_stack:
            raise IndexError("Cannot pop from an empty cleanup stack")

        if index is None:
            return self.cleanup_stack.pop()
        else:
            if 0 <= index < len(self.cleanup_stack):
                return self.cleanup_stack.pop(index)
            else:
                raise IndexError(f"Cleanup stack index {index} out of range")

    def set_selenium_controller(
        self, controller: Union[EdgeSeleniumController, FirefoxSeleniumController]
    ) -> int:
        """
        Set the selenium controller for cleanup

        Args:
            controller: The selenium controller to set

        Returns:
            int: The index of the added task for later reference
        """
        self.selenium_controller = controller
        # Add the driver quit function to the cleanup stack
        return self.add_cleanup_task(self.selenium_controller.quit_driver)

    def run_cleanup(self) -> None:
        """Execute all cleanup tasks in reverse order (LIFO)"""
        for task in reversed(self.cleanup_stack):
            try:
                function = task["function"]
                args = task.get("args", ())
                kwargs = task.get("kwargs", {})
                function(*args, **kwargs)
            except Exception as e:
                print(f"Error during cleanup: {e}")

        self.cleanup_stack = []

