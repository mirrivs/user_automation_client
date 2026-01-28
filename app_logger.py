import os
import sys
import yaml
import logging
import logging.config


parent_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(parent_dir, "config.yml")


def load_config(config_file):
    with open(config_file, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as ex:
            print(f"Error reading configuration from '{config_file}': {ex}")
            sys.exit(1)


def configure_logger(cfg):
    if "logging" in cfg:
        log_folder_path = cfg["logging"]["handlers"]["file"]["filename"]
        log_folder = os.path.dirname(log_folder_path)
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        logging.config.dictConfig(cfg["logging"])


cfg = load_config(config_file)
configure_logger(cfg)
app_logger = logging.getLogger("autoconfig")
