from selenium import webdriver

from consts.timeout import DEFAULT_TIMEOUT
from lib.selenium.cancellable_wait import CancellableWebDriverWait


class SeleniumDriver:
    def __init__(self, driver: (webdriver.Firefox | webdriver.Edge)):
        self.driver: webdriver.Firefox | webdriver.Edge = driver

    def maximize_driver_window(self):
        self.driver.maximize_window()

    def quit_driver(self):
        self.driver.quit()

    def wait(self, timeout: float = DEFAULT_TIMEOUT):
        return CancellableWebDriverWait(self.driver, timeout)
