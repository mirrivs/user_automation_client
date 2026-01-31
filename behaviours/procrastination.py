import platform
import time
import random
from datetime import datetime

from app_config import automation_config
from app_logger import app_logger
from cleanup_manager import CleanupManager

from utils.selenium_utils import EdgeSeleniumController, FirefoxSeleniumController
from utils.behaviour import BaseBehaviour, BehaviourCategory

from scripts_pyautogui.browser_utils.browser_utils import BrowserUtils


def weighted_random_choice(weights_dict):
    """Select a random key from a dictionary based on weighted probabilities."""
    if not weights_dict:
        raise ValueError("Weights dictionary cannot be empty")

    total_weight = sum(weights_dict.values())
    if total_weight <= 0:
        raise ValueError("Total weight must be positive")

    random_number = random.uniform(0, total_weight)
    cumulative_weight = 0
    
    for preference, weight in weights_dict.items():
        cumulative_weight += weight
        if random_number <= cumulative_weight:
            return preference

    return list(weights_dict.keys())[-1]


class BehaviourProcrastination(BaseBehaviour):
    """
    Behaviour for procrastinating on scrolling kitten images or watching YouTube shorts.
    """

    # Class-level metadata
    id = "procrastination"
    display_name = "Procrastination"
    category = BehaviourCategory.IDLE
    description = "Simulates procrastination activities like browsing"

    def __init__(self, cleanup_manager: CleanupManager = None):
        super().__init__(cleanup_manager)
        
        if cleanup_manager is not None:
            self.user = automation_config["general"]["user"]
            self.behaviour_cfg = automation_config["behaviours"]["procrastination"]
        else:
            self.user = None
            self.behaviour_cfg = None
            
        self.selenium_controller = None

    def _is_available(self) -> bool:
        return self.os_type in ["Windows", "Linux", "Darwin"]

    def run_behaviour(self):
        app_logger.info("Starting procrastination behaviour")

        self.selenium_controller = (
            FirefoxSeleniumController()
            if self.os_type == "Linux"
            else EdgeSeleniumController()
        )

        self.cleanup_manager.selenium_controller = self.selenium_controller
        self.cleanup_manager.add_cleanup_task(self.selenium_controller.quit_driver)

        self.selenium_controller.maximize_driver_window()
        time.sleep(3)

        procrastination_time = random.uniform(
            self.behaviour_cfg["min_duration"], self.behaviour_cfg["max_duration"])
        start_time = datetime.now()

        preferences = self.behaviour_cfg["preference"]
        selected_preference = weighted_random_choice(preferences)

        app_logger.info(f"Selected procrastination preference: {selected_preference}")

        if selected_preference == "youtube":
            BrowserUtils.search_by_url("youtube.com")
            time.sleep(3)

            watch_duration = procrastination_time - (datetime.now() - start_time).total_seconds()
            self.selenium_controller.procrastinate_watch_youtube_shorts(watch_duration)

        elif selected_preference == "kittens":
            BrowserUtils.search_by_url("kittens")
            time.sleep(3)

            if self.os_type == "Linux":
                self.selenium_controller.accept_google_cookies()
                time.sleep(2)

            scroll_duration = procrastination_time - (datetime.now() - start_time).total_seconds()
            self.selenium_controller.procrastinate_scroll_images(scroll_duration)
            time.sleep(2)
        else:
            app_logger.warning(f"Unknown procrastination preference: {selected_preference}")

        app_logger.info("Completed procrastination behaviour")