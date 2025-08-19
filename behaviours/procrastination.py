import platform
import time
import random
from datetime import datetime

from app_config import app_config
from utils.app_logger import app_logger
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
    """
    os_type = platform.system()

    selenium_controller = FirefoxSeleniumController() if os_type == "Linux" else EdgeSeleniumController()
    cleanup_manager.selenium_controller = selenium_controller
    
    selenium_controller.maximize_driver_window()

    time.sleep(3)

    procrastination_time = random.uniform(
        behaviour_cfg["procrastination_min_time"], behaviour_cfg["procrastination_max_time"])
    start_time = datetime.now()

    if random.uniform(0, 1) < behaviour_cfg["procrastination_preference"]:
        # Procrastinate on youtube
        BrowserUtils.search_by_url("youtube.com")
        time.sleep(3)

        watch_duration = procrastination_time - (datetime.now() - start_time).total_seconds()
        selenium_controller.procrastinate_watch_youtube_shorts(watch_duration)
    else:
        # Procrastinate on cats
        BrowserUtils.search_by_url("kittens")
        time.sleep(3)

        if os_type == "Linux":
            selenium_controller.accept_google_cookies()
            time.sleep(2)

        scroll_duration = procrastination_time - (datetime.now() - start_time).total_seconds()
        selenium_controller.procrastinate_scroll_images(scroll_duration)

        time.sleep(2)