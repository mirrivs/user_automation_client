import os
from utils.config_handler import load_config

from models.config import AppConfig

parent_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(parent_dir, "config.yml")

app_config: AppConfig = load_config(config_file)
