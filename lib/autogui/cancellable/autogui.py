import threading
import time
import typing
from dataclasses import dataclass, field
from typing import Callable, Optional

import pyautogui
from exceptions import OperationCancelled

T = typing.TypeVar("T")

POLL_FREQUENCY: float = 0.1


@dataclass
class Ref(typing.Generic[T]):
    value: Optional[T] = None

    def __bool__(self):
        return self.value is not None


@dataclass
class _TaskHandle:
    thread: threading.Thread
    event: threading.Event = field(default_factory=threading.Event)
    exception: Optional[Exception] = None
    result: Ref = field(default_factory=Ref)


class CancellableAutogui:
    def __init__(self, poll_frequency: float = POLL_FREQUENCY):
        self._global_event = threading.Event()
        self._poll = poll_frequency
        self._tasks: dict[str, _TaskHandle] = {}
        self._lock = threading.Lock()
        self._local = threading.local()

    def __repr__(self):
        with self._lock:
            active = sum(1 for h in self._tasks.values() if h.thread.is_alive())
        return f"<CancellableAutogui (active_tasks={active})>"

    def __getattr__(self, name):
        func = getattr(pyautogui, name)

        def wrapper(*args, **kwargs):
            return self._run_cancellable(func, *args, **kwargs)

        return wrapper

    @property
    def is_running(self) -> bool:
        with self._lock:
            return any(h.thread.is_alive() for h in self._tasks.values())

    @property
    def task_names(self) -> list[str]:
        with self._lock:
            return list(self._tasks.keys())

    def start(self, name, method, *args, **kwargs) -> Ref:
        with self._lock:
            if name in self._tasks and self._tasks[name].thread.is_alive():
                raise RuntimeError(f"Task {name!r} is already running")

        handle = _TaskHandle(
            thread=threading.Thread(
                target=self._execute,
                args=(name, method, *args),
                kwargs=kwargs,
                daemon=True,
            )
        )

        with self._lock:
            self._tasks[name] = handle

        handle.thread.start()
        return handle.result  # <-- return the ref

    def _execute(self, name, method, *args, **kwargs):
        with self._lock:
            handle = self._tasks[name]
        self._local.event = handle.event
        try:
            handle.result.value = method(self, *args, **kwargs)
        except Exception as e:
            handle.exception = e

    def cancel(self, name: Optional[str] = None) -> None:
        """Cancel a single task by name, or all tasks if no name is given."""
        if name is None:
            self._global_event.set()
            return

        with self._lock:
            handle = self._tasks.get(name)

        if handle is None:
            raise KeyError(f"No task named {name!r}")

        handle.event.set()

    def join(self, name: Optional[str] = None, timeout: Optional[float] = None):
        if name is not None:
            with self._lock:
                handle = self._tasks.get(name)
            if handle is None:
                raise KeyError(f"No task named {name!r}")
            handle.thread.join(timeout=timeout)
            self._raise_if_failed(handle)
            return handle.result

        # join all
        with self._lock:
            handles = dict(self._tasks)

        for handle in handles.values():
            handle.thread.join(timeout=timeout)

        exceptions = [
            h.exception for h in handles.values() if h.exception and not isinstance(h.exception, OperationCancelled)
        ]
        if exceptions:
            raise exceptions[0]

        return {name: h.result for name, h in handles.items()}

    def reset(self, name: Optional[str] = None) -> None:
        """Reset a specific task or all state."""
        with self._lock:
            if name is not None:
                self._tasks.pop(name, None)
            else:
                self._global_event.clear()
                self._tasks.clear()

    def sleep(self, duration: float) -> None:
        """Cancellation-aware sleep."""
        end = time.time() + duration
        while time.time() < end:
            self._check()
            time.sleep(min(self._poll, end - time.time()))

    def _check(self) -> None:
        if self._global_event.is_set():
            raise OperationCancelled("All operations cancelled")

        event: Optional[threading.Event] = getattr(self._local, "event", None)
        if event is not None and event.is_set():
            raise OperationCancelled("Task cancelled")

    def _run_cancellable(self, func, *args, **kwargs):
        result = None
        exception = None

        def target():
            nonlocal result, exception
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                exception = e

        thread = threading.Thread(target=target, daemon=True)
        thread.start()

        while thread.is_alive():
            self._check()
            thread.join(timeout=self._poll)

        if exception:
            raise exception

        return result

    def race(
        self, tasks: dict[str, Callable[["CancellableAutogui"], T]], timeout: Optional[float] = None
    ) -> tuple[str, T]:
        for name, method in tasks.items():
            self.start(name, method)

        done_event = threading.Event()
        winner: Optional[str] = None

        def _monitor(name: str, handle: _TaskHandle):
            nonlocal winner
            handle.thread.join()
            with self._lock:
                if winner is None:
                    winner = name
                    done_event.set()

        monitors = []
        for name, handle in self._tasks.items():
            if name in tasks:
                t = threading.Thread(target=_monitor, args=(name, handle), daemon=True)
                t.start()
                monitors.append(t)

        done_event.wait(timeout=timeout)

        for name in tasks:
            if name != winner:
                self.cancel(name)

        for name in tasks:
            self.join(name)

        if winner is None:
            raise TimeoutError("No task completed within timeout")

        with self._lock:
            handle = self._tasks[winner]

        return winner, handle.result.value

    @staticmethod
    def _raise_if_failed(handle: _TaskHandle) -> None:
        if handle.exception and not isinstance(handle.exception, OperationCancelled):
            raise handle.exception
