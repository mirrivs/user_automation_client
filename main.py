#! ./env/bin/python3

import atexit
import os
import sys

# Custom imports
from app_config import app_config
from utils.app_logger import app_logger
from utils.config_handler import clear_behaviour_cfg
from system_tray import SystemTrayApp
from user_automation_manager import UserAutomationManager

if len(sys.argv) > 2 and sys.argv[2].lower() not in os.getlogin().lower():
    os._exit(0)


parent_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(parent_dir, "config.yml")


def main():
    user_automation_manager = UserAutomationManager(app_config)

    tray_app = SystemTrayApp(user_automation_manager)

    user_automation_manager.start()

    # atexit.register(clear_behaviour_cfg, config_file)

    sys.exit(tray_app.run())


if __name__ == "__main__":
    main()
