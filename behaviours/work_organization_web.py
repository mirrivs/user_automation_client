import platform
import time

from app_config import app_config
from app_logger import app_logger
from cleanup_manager import CleanupManager

# Utilities imports
from utils.selenium_utils import EdgeSeleniumController, FirefoxSeleniumController
from utils.behaviour_utils import BehaviourThread

# Scripts imports
from scripts_pyautogui.browser_utils.browser_utils import BrowserUtils


class BehaviourWorkOrganizationWeb(BehaviourThread):
    """
    Behaviour for browsing organization website with instant stop capability.

    This class can be directly instantiated and started from the behaviour manager.
    """

    # Behaviour metadata
    name = "work_organization_web"
    display_name = "Organization Web"
    category = "IDLE"
    description = "Simulates browsing organization website"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)
        self.os_type = platform.system()
        self.user = app_config["behaviour"]["general"]["user"]
        self.selenium_controller = None

    def run_behaviour(self):
        """Main behaviour execution - can be interrupted at any time"""
        app_logger.info("Starting work_organization_web behaviour")

        # Initialize selenium controller
        self.selenium_controller = (
            FirefoxSeleniumController()
            if self.os_type == "Linux"
            else EdgeSeleniumController()
        )

        # Register selenium controller with cleanup manager
        self.cleanup_manager.selenium_controller = self.selenium_controller
        self.cleanup_manager.add_cleanup_task(self.selenium_controller.quit_driver)

        # Execute automation steps
        self.selenium_controller.maximize_driver_window()
        time.sleep(4)

        BrowserUtils.search_by_url(
            app_config["behaviour"]["general"]["organization_web_url"]
        )
        time.sleep(4)

        # This long operation can be interrupted instantly
        self.selenium_controller.browse_organization_website(45)

        app_logger.info("Completed work_organization_web behaviour")
