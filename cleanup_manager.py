from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union

from lib.selenium.selenium_controller import (
    EdgeSeleniumController,
    FirefoxSeleniumController,
)
from src.logger import app_logger


@dataclass(slots=True)
class CleanupTask:
    function: Callable[..., Any]
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    label: Optional[str] = None
    active: bool = True

    def run(self) -> None:
        if not self.active:
            return

        self.active = False
        self.function(*self.args, **self.kwargs)

    def discard(self) -> None:
        self.active = False


class CleanupManager:
    def __init__(self):
        self.selenium_controller: Optional[Union[EdgeSeleniumController, FirefoxSeleniumController]] = None
        self._tasks: list[CleanupTask] = []

    @property
    def tasks(self) -> list[CleanupTask]:
        return list(self._tasks)

    def add_cleanup_task(
        self,
        func: Callable[..., Any],
        *args: Any,
        label: Optional[str] = None,
        **kwargs: Any,
    ) -> CleanupTask:
        task = CleanupTask(function=func, args=args, kwargs=kwargs, label=label)
        self._tasks.append(task)
        return task

    def remove_task(self, task: CleanupTask) -> CleanupTask:
        self._tasks.remove(task)
        return task

    def pop_cleanup_task(self, index: Optional[int] = None) -> CleanupTask:
        if not self._tasks:
            raise IndexError("Cannot pop from an empty cleanup stack")

        if index is None:
            return self._tasks.pop()

        if 0 <= index < len(self._tasks):
            return self._tasks.pop(index)

        raise IndexError(f"Cleanup stack index {index} out of range")

    def run_task(self, task: CleanupTask, remove: bool = True) -> None:
        if remove:
            try:
                self.remove_task(task)
            except ValueError:
                pass

        try:
            task.run()
        except Exception as ex:
            task_name = task.label or getattr(task.function, "__name__", repr(task.function))
            app_logger.error(f"Error during cleanup task '{task_name}': {ex}", exc_info=True)

    def discard_task(self, task: CleanupTask, remove: bool = True) -> None:
        if remove:
            try:
                self.remove_task(task)
            except ValueError:
                pass
        task.discard()

    def set_selenium_controller(self, controller: Union[EdgeSeleniumController, FirefoxSeleniumController]) -> CleanupTask:
        self.selenium_controller = controller
        return self.add_cleanup_task(controller.quit_driver, label="quit_driver")

    def run_cleanup(self) -> None:
        while self._tasks:
            task = self._tasks.pop()
            self.run_task(task, remove=False)
