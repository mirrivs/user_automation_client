import os
from config_handler import load_config, save_config

from models.config import AppConfig

parent_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(parent_dir, "config.yml")

def save_app_config(config: dict):
  save_config(config_file, config)

app_config: AppConfig = load_config(config_file)
