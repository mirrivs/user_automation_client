from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait


from consts.timeout import DEFAULT_TIMEOUT


class SeleniumDriver:
    def __init__(self, driver: (webdriver.Firefox | webdriver.Edge)):
        self.driver: webdriver.Firefox | webdriver.Edge = driver

    def maximize_driver_window(self):
        """
        Maximize driver window\n
        """
        self.driver.maximize_window()

    def quit_driver(self):
        """
        Quit the WebDriver and close all associated windows
        """
        self.driver.quit()

    def wait(self, timeout: float = DEFAULT_TIMEOUT):
        """
        Wait for the set time for action to be complete
        """
        return WebDriverWait(self.driver, timeout)
