from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from consts.timeout import DEFAULT_TIMEOUT
from lib.cancellable_futures import check as cancellable_check
from lib.cancellable_futures import sleep
from lib.selenium.cancellable_wait import CancellableWebDriverWait


class SeleniumDriver:
    def __init__(self, driver: (webdriver.Firefox | webdriver.Edge)):
        self.driver: webdriver.Firefox | webdriver.Edge = driver

    def check_cancellation(self) -> None:
        try:
            cancellable_check()
        except LookupError:
            pass

    def maximize_driver_window(self):
        self.check_cancellation()
        self.driver.maximize_window()
        self.check_cancellation()

    def quit_driver(self):
        self.driver.quit()

    def wait(self, timeout: float = DEFAULT_TIMEOUT):
        return CancellableWebDriverWait(self.driver, timeout)

    def find_element(self, *args, **kwargs) -> WebElement:
        self.check_cancellation()
        element = self.driver.find_element(*args, **kwargs)
        self.check_cancellation()
        return element

    def scroll_into_view(self, element: WebElement) -> None:
        self.check_cancellation()
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
            element,
        )
        self.check_cancellation()

    def click_element(self, element: WebElement) -> None:
        self.check_cancellation()
        try:
            self.scroll_into_view(element)
            element.click()
        except ElementClickInterceptedException:
            self.check_cancellation()
            self.driver.execute_script("arguments[0].focus();", element)
            self.driver.execute_script("arguments[0].click();", element)
        self.check_cancellation()

    def focus_element(self, element: WebElement) -> None:
        self.check_cancellation()
        try:
            self.click_element(element)
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].focus();", element)
            self.check_cancellation()

    def type_text(self, element: WebElement, value: str, clear_first: bool = False, keystroke_delay: float = 0.0):
        self.check_cancellation()
        self.focus_element(element)
        sleep(0.5)

        if clear_first:
            try:
                element.clear()
            except Exception:
                pass

            self.check_cancellation()
            element.send_keys(Keys.CONTROL, "a")
            self.check_cancellation()
            element.send_keys(Keys.DELETE)
            sleep(0.2)

        for char in value:
            self.check_cancellation()
            element.send_keys(char)
            if keystroke_delay > 0:
                sleep(keystroke_delay)
