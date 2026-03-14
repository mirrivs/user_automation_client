"""Cancellable thread pool executor with cooperative cancellation.

A thin wrapper around ``concurrent.futures.ThreadPoolExecutor`` that adds
cooperative cancellation via ``threading.Event``.  Tasks call ``check()``
at safe points; if the task (or the entire pool) has been cancelled, an
``OperationCancelled`` exception is raised.

Usage::

    pool = CancellableThreadPoolExecutor()

    # block for result
    data = pool.submit(fetch_page, url).result(timeout=10)

    # cancel a specific task
    pool.submit(long_poll, name="poller").cancel()

    # race — first to finish wins, rest are cancelled
    winner, value = pool.race({"a": fn_a, "b": fn_b}, timeout=5)

    # cancel everything
    pool.cancel()

Inside a running task::

    from cancellable_executor import check, sleep

    def my_task():
        while True:
            check()          # raises OperationCancelled if cancelled
            do_work()
            sleep(0.5)       # cancellation-aware sleep
"""

from __future__ import annotations

import contextvars
import threading
import time
import typing
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Callable, Generic, Optional

from lib.cancellable_futures.exceptions import OperationCancelled

T = typing.TypeVar("T")

DEFAULT_POLL_FREQUENCY: float = 0.05


# -- task handle --------------------------------------------------------------


class TaskHandle(Generic[T]):
    """Thin wrapper around a ``Future`` that adds cooperative cancellation."""

    def __init__(self, name: str, future: Future[T], event: threading.Event):
        self._name = name
        self._future = future
        self._event = event

    def __repr__(self):
        return f"<TaskHandle {self._name!r} done={self.done}>"

    @property
    def name(self) -> str:
        return self._name

    @property
    def done(self) -> bool:
        return self._future.done()

    @property
    def exception(self) -> Optional[BaseException]:
        if not self._future.done():
            return None
        return self._future.exception()

    @property
    def future(self) -> Future[T]:
        """The underlying ``concurrent.futures.Future``."""
        return self._future

    def result(self, timeout: Optional[float] = None) -> T:
        """Block until done and return the result (re-raises task exceptions)."""
        return self._future.result(timeout=timeout)

    def cancel(self) -> TaskHandle[T]:
        """Signal the task to stop cooperatively.  Returns *self* for chaining."""
        self._event.set()
        return self

    def add_done_callback(self, fn: Callable[[Future[T]], None]) -> None:
        self._future.add_done_callback(fn)


# -- executor -----------------------------------------------------------------


class CancellableThreadPoolExecutor:
    """A ``ThreadPoolExecutor`` with cooperative cancellation.

    Args:
        max_workers:     Forwarded to ``ThreadPoolExecutor``.
        poll_frequency:  Granularity (seconds) of cancellation checks inside
                         ``sleep()``.  Lower values = more responsive
                         cancellation, higher CPU usage.
                         Default 50ms
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        poll_frequency: float = DEFAULT_POLL_FREQUENCY,
    ):
        self._poll = poll_frequency
        self._global_event = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: dict[str, TaskHandle] = {}
        self._lock = threading.Lock()
        self._local = threading.local()

    def __repr__(self):
        with self._lock:
            active = sum(1 for t in self._tasks.values() if not t.done)
        return f"<CancellableThreadPoolExecutor active={active}>"

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.shutdown(wait=True)

    # -- submit ---------------------------------------------------------------

    def submit(self, fn: Callable[..., T], *args, name: Optional[str] = None, **kwargs) -> TaskHandle[T]:
        """Submit *fn* to run in the pool.  Returns a ``TaskHandle``.

        Args:
            fn:       Callable to execute.
            *args:    Positional arguments forwarded to *fn*.
            name:     Optional label (defaults to ``fn.__name__``).
                      Re-using a name while a task is still alive raises
                      ``RuntimeError``.
            **kwargs: Keyword arguments forwarded to *fn*.
        """
        task_name = name or getattr(fn, "__name__", repr(fn))

        with self._lock:
            existing = self._tasks.get(task_name)
            if existing and not existing.done:
                raise RuntimeError(f"Task {task_name!r} is already running")

        event = threading.Event()
        future = self._executor.submit(self._run, event, fn, *args, **kwargs)
        handle = TaskHandle(task_name, future, event)

        with self._lock:
            self._tasks[task_name] = handle

        return handle

    def _run(self, event: threading.Event, fn, *args, **kwargs):
        self._local.event = event
        _current_executor.set(self)
        return fn(*args, **kwargs)

    # -- cancellation ---------------------------------------------------------

    def cancel(self, name: Optional[str] = None) -> None:
        """Cancel one task by *name*, or **all** tasks if *name* is ``None``."""
        if name is None:
            self._global_event.set()
            return

        with self._lock:
            handle = self._tasks.get(name)
        if handle is None:
            raise KeyError(f"No task named {name!r}")
        handle.cancel()

    def check(self) -> None:
        """Raise ``OperationCancelled`` if the calling task has been cancelled.

        Call this at safe cancellation points inside your task functions.
        """
        if self._global_event.is_set():
            raise OperationCancelled("All tasks cancelled")

        event: Optional[threading.Event] = getattr(self._local, "event", None)
        if event is not None and event.is_set():
            raise OperationCancelled("Task cancelled")

    def sleep(self, duration: float) -> None:
        """Cancellation-aware ``time.sleep``."""
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            self.check()
            time.sleep(min(self._poll, deadline - time.monotonic()))

    # -- bulk operations ------------------------------------------------------

    def join(self, timeout: Optional[float] = None) -> dict[str, TaskHandle]:
        """Wait for every tracked task to finish."""
        with self._lock:
            tasks = dict(self._tasks)

        futures = {t.future: t for t in tasks.values()}
        for _ in as_completed(futures, timeout=timeout):
            pass

        for t in tasks.values():
            exc = t.exception
            if exc and not isinstance(exc, OperationCancelled):
                raise exc

        return tasks

    def race(self, callables: dict[str, Callable], timeout: Optional[float] = None) -> tuple[str, T]:
        """Start all *callables*; return ``(winner_name, result)`` for the first to finish.

        The remaining tasks are cancelled automatically.
        """
        started = {name: self.submit(fn, name=name) for name, fn in callables.items()}
        future_to_name = {t.future: name for name, t in started.items()}

        for future in as_completed(future_to_name, timeout=timeout):
            winner = future_to_name[future]

            for name, t in started.items():
                if name != winner:
                    t.cancel()

            exc = future.exception()
            if exc and not isinstance(exc, OperationCancelled):
                raise exc

            return winner, future.result()

        raise TimeoutError("Race timed out")

    # -- lifecycle ------------------------------------------------------------

    def reset(self, name: Optional[str] = None) -> None:
        """Remove finished tasks from tracking.  Clears global cancellation if
        *name* is ``None``."""
        with self._lock:
            if name is not None:
                self._tasks.pop(name, None)
            else:
                self._global_event.clear()
                self._tasks.clear()

    def shutdown(self, wait: bool = True) -> None:
        """Cancel all tasks and shut down the underlying thread pool."""
        self._global_event.set()
        self._executor.shutdown(wait=wait)


# -- context-var glue (used by module-level helpers) --------------------------

_current_executor: contextvars.ContextVar[CancellableThreadPoolExecutor] = contextvars.ContextVar("_current_executor")


def get_executor() -> CancellableThreadPoolExecutor:
    """Return the ``CancellableThreadPoolExecutor`` bound to the current task thread."""
    return _current_executor.get()


def check() -> None:
    """Module-level shortcut — calls ``check()`` on the current executor."""
    get_executor().check()


def sleep(duration: float) -> None:
    """Module-level shortcut — calls ``sleep()`` on the current executor."""
    get_executor().sleep(duration)
