import platform
import time

from app_config import app_config
from utils.app_logger import app_logger
from cleanup_manager import CleanupManager

# Utilities imports
from utils.selenium_utils import EdgeSeleniumController, FirefoxSeleniumController 

# Scripts imports
from scripts_pyautogui.browser_utils.browser_utils import BrowserUtils


def behaviour_work_organization_web(cleanup_manager: CleanupManager):
    """
    This behaviour browses organization website
    """
    os_type = platform.system()

    user = app_config["behaviour"]["general"]["user"]

    selenium_controller = FirefoxSeleniumController() if os_type == "Linux" else EdgeSeleniumController()
    cleanup_manager.selenium_controller = selenium_controller
    
    selenium_controller.maximize_driver_window()
    time.sleep(4)

    BrowserUtils.search_by_url(app_config["behaviour"]["general"]["organization_web_url"])
    time.sleep(4)

    selenium_controller.browse_organization_website(45)