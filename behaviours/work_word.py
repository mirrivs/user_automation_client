import sys
import os
import pyautogui as pag

# 
# Unfinished 
# 

# Append to path for custom imports
BEHAVIOUR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BEHAVIOUR_DIR)

TOP_DIR = os.path.join(BEHAVIOUR_DIR, "..")
sys.path.append(TOP_DIR)

TEMPLATES_DIR = os.path.join(BEHAVIOUR_DIR, "templates")

# Custom imports
from app_config import app_config
from utils.app_logger import app_logger
import utils.config_handler as config_handler

# Scripts imports
from scripts_pyautogui.os_utils import os_utils
from scripts_pyautogui.office_utils import office_utils




def behaviour_work_word():
    """
    This behaviour generates or responds to predefined email conversation using Roundcube web client 
    """
    user = app_config["behaviour"]["general"]["user"]

    office_utils.start_app("word")
