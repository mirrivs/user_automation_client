import platform
import time
import random
from datetime import datetime

from app_config import app_config
from app_logger import app_logger
from cleanup_manager import CleanupManager

# Utilities imports
from utils.selenium_utils import EdgeSeleniumController, FirefoxSeleniumController
from utils.behaviour_utils import BehaviourThread

# Scripts imports
from scripts_pyautogui.browser_utils.browser_utils import BrowserUtils


def weighted_random_choice(weights_dict):
    """
    Select a random key from a dictionary based on weighted probabilities.

    Args:
        weights_dict: Dictionary with keys as choices and values as weights
                     Example: {"youtube": 3, "kittens": 1} means youtube has 3x chance

    Returns:
        Selected key based on weighted probability
    """
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


class BehaviourProcrastination(BehaviourThread):
    """
    Behaviour for procrastinating on scrolling kitten images or watching YouTube shorts.

    This class can be directly instantiated and started from the behaviour manager.
    Uses weighted selection based on preference values.
    """

    # Behaviour metadata
    name = "procrastination"
    display_name = "Procrastination"
    category = "IDLE"
    description = "Simulates procrastination activities like browsing"

    def __init__(self, cleanup_manager: CleanupManager):
        super().__init__(cleanup_manager)
        self.os_type = platform.system()
        self.user = app_config["behaviour"]["general"]["user"]
        self.behaviour_cfg = app_config["behaviour"]["behaviours"]["procrastination"]
        self.selenium_controller = None

    def run_behaviour(self):
        """Main behaviour execution - can be interrupted at any time"""
        app_logger.info("Starting procrastination behaviour")

        self.selenium_controller = (
            FirefoxSeleniumController()
            if self.os_type == "Linux"
            else EdgeSeleniumController()
        )

        # Register selenium controller with cleanup manager
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
