import logging
import logging.config
import os

from resource_path import resource_path
from src.config.config_handler import load_config

config_file_path = resource_path("config.yml")


def configure_logger(cfg):
    if "logging" in cfg:
        log_folder_path = cfg["logging"]["handlers"]["file"]["filename"]
        log_folder = os.path.dirname(log_folder_path)
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        logging.config.dictConfig(cfg["logging"])


cfg = load_config(config_file_path)
configure_logger(cfg)
app_logger = logging.getLogger("autoconfig")
