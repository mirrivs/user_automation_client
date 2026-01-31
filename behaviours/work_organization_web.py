import platform
import time

from app_config import app_config
from app_logger import app_logger
from cleanup_manager import CleanupManager

from utils.selenium_utils import EdgeSeleniumController, FirefoxSeleniumController
from utils.behaviour import BaseBehaviour, BehaviourCategory

from scripts_pyautogui.browser_utils.browser_utils import BrowserUtils


class BehaviourWorkOrganizationWeb(BaseBehaviour):
    """
    Behaviour for browsing organization website.
    """

    # Class-level metadata
    id = "work_organization_web"
    display_name = "Organization Web"
    category = BehaviourCategory.IDLE
    description = "Simulates browsing organization website"

    def __init__(self, cleanup_manager: CleanupManager = None):
        super().__init__(cleanup_manager)
        
        if cleanup_manager is not None:
            self.user = app_config["behaviour"]["general"]["user"]
            self.behaviour_general = app_config["behaviour"]["general"]
        else:
            self.user = None
            self.behaviour_general = None
            
        self.selenium_controller = None

    def _is_available(self) -> bool:
        return self.os_type in ["Windows", "Linux", "Darwin"]

    def run_behaviour(self):
        app_logger.info("Starting work_organization_web behaviour")

        self.selenium_controller = (
            FirefoxSeleniumController()
            if self.os_type == "Linux"
            else EdgeSeleniumController()
        )

        self.cleanup_manager.selenium_controller = self.selenium_controller
        self.cleanup_manager.add_cleanup_task(self.selenium_controller.quit_driver)

        self.selenium_controller.maximize_driver_window()
        time.sleep(4)

        BrowserUtils.search_by_url(self.behaviour_general["organization_web_url"])
        time.sleep(4)

        self.selenium_controller.browse_organization_website(45)

        app_logger.info("Completed work_organization_web behaviour")