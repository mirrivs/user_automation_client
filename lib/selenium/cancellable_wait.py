"""Drop-in replacement for ``selenium.webdriver.support.wait.WebDriverWait``
that is aware of :class:`CancellableThreadPoolExecutor` cancellation.

The only behavioural difference from the upstream class is that each poll
cycle calls ``check()`` from ``cancellable_executor``, so an
``OperationCancelled`` exception will be raised promptly when the task is
cancelled — instead of blocking until the full Selenium timeout expires.

If used outside of a ``CancellableThreadPoolExecutor`` task (i.e. no
executor is bound to the current thread), it behaves identically to the
standard ``WebDriverWait``.

Usage::

    from cancellable_wait import CancellableWebDriverWait

    class SeleniumDriver:
        def wait(self, timeout=10):
            return CancellableWebDriverWait(self.driver, timeout)

    # Then everywhere:
    self.wait().until(EC.element_to_be_clickable((By.XPATH, "//button")))
    # ^ will raise OperationCancelled promptly if the task is cancelled
"""

import time

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.wait import WebDriverWait

from lib.cancellable_futures import check as _check
from lib.cancellable_futures import get_executor
from lib.cancellable_futures import sleep as _sleep

POLL_FREQUENCY: float = 0.5
IGNORED_EXCEPTIONS: tuple[type[Exception]] = (NoSuchElementException,)


def _in_executor() -> bool:
    """Return True if the current thread is running inside a CancellableThreadPoolExecutor."""
    try:
        get_executor()
        return True
    except LookupError:
        return False


class CancellableWebDriverWait(WebDriverWait):
    def until(self, method, message=""):
        screen = None
        stacktrace = None
        cancellable = _in_executor()

        end_time = time.monotonic() + self._timeout
        while True:
            if cancellable:
                _check()

            try:
                value = method(self._driver)
                if value:
                    return value
            except self._ignored_exceptions as exc:
                screen = getattr(exc, "screen", None)
                stacktrace = getattr(exc, "stacktrace", None)

            if time.monotonic() > end_time:
                break

            if cancellable:
                _sleep(self._poll)
            else:
                time.sleep(self._poll)

        raise TimeoutException(message, screen, stacktrace)

    def until_not(self, method, message=""):
        cancellable = _in_executor()

        end_time = time.monotonic() + self._timeout
        while True:
            if cancellable:
                _check()

            try:
                value = method(self._driver)
                if not value:
                    return value
            except self._ignored_exceptions:
                return True

            if time.monotonic() > end_time:
                break

            if cancellable:
                _sleep(self._poll)
            else:
                time.sleep(self._poll)

        raise TimeoutException(message)
