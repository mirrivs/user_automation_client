import platform
import time
import random
from datetime import datetime

from app_config import app_config
from app_logger import app_logger
from cleanup_manager import CleanupManager

# Utilities imports
from utils.selenium_utils import EdgeSeleniumController, FirefoxSeleniumController 

# Scripts imports
from scripts_pyautogui.browser_utils.browser_utils import BrowserUtils

user = app_config["behaviour"]["general"]["user"]
behaviour_cfg = app_config["behaviour"]["behaviours"]["procrastination"]

def behaviour_procrastination(cleanup_manager: CleanupManager):
    """
    This behaviour procrastinates on scrolling on kitten images or youtube shorts using selenium.
    Uses weighted selection based on preference values.
    """
    os_type = platform.system()

    selenium_controller = FirefoxSeleniumController() if os_type == "Linux" else EdgeSeleniumController()
    cleanup_manager.selenium_controller = selenium_controller
    
    selenium_controller.maximize_driver_window()

    time.sleep(3)

    procrastination_time = random.uniform(
        behaviour_cfg["duration_min"], behaviour_cfg["duration_max"])
    start_time = datetime.now()

    preferences = behaviour_cfg["preference"]
    selected_preference = weighted_random_choice(preferences)
    
    app_logger.info(f"Selected procrastination preference: {selected_preference}")

    if selected_preference == "youtube":
        BrowserUtils.search_by_url("youtube.com")
        time.sleep(3)

        watch_duration = procrastination_time - (datetime.now() - start_time).total_seconds()
        selenium_controller.procrastinate_watch_youtube_shorts(watch_duration)

    elif selected_preference == "kittens":
        BrowserUtils.search_by_url("kittens")
        time.sleep(3)

        if os_type == "Linux":
            selenium_controller.accept_google_cookies()
            time.sleep(2)

        scroll_duration = procrastination_time - (datetime.now() - start_time).total_seconds()
        selenium_controller.procrastinate_scroll_images(scroll_duration)

        time.sleep(2)
    else:
        app_logger.warning(f"Unknown procrastination preference: {selected_preference}")

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