import os
from config_handler import load_config, save_config

from models.config import AppConfig, AutomationConfig

parent_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(parent_dir, "config.yml")


app_config: AppConfig = load_config(config_file)
automation_config: AutomationConfig = app_config.get("automation", {})


def save_app_config(config: dict):
    save_config(config_file, config)


def get_app_config() -> AppConfig:
    return load_config(config_file)
