import os
import sys
from typing import Any

import yaml


def load_config(config_file: str):
    config_file = os.path.abspath(config_file)
    with open(config_file, "r", encoding="utf-8") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as ex:
            print(f"Error reading configuration from '{config_file}': {ex}")
            sys.exit(1)


def save_config(path: str, config: dict[str, Any]) -> None:
    """
    Write new config to config file
    """
    config_file = os.path.abspath(path)
    with open(config_file, "w", encoding="utf-8") as stream:
        try:
            yaml.dump(config, stream, default_flow_style=False)
        except yaml.YAMLError as ex:
            print(f"Error writing configuration to '{config_file}': {ex}")
            sys.exit(1)


def clear_behaviour_cfg(config_file):
    """
    Removes behaviour key from config file
    """
    config: dict = load_config(config_file)
    if "behaviour" in config:
        config.pop("behaviour")
    save_config(config_file, config)
