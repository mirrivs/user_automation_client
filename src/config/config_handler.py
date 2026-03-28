import os
import sys
from typing import Any, cast

import yaml

from behaviour.ids import BehaviourId
from src.config.models.config import AppConfig, AutomationConfig


def load_config(config_file: str) -> AppConfig:
    config_file = os.path.abspath(config_file)
    with open(config_file, "r", encoding="utf-8") as stream:
        try:
            config = yaml.safe_load(stream) or {}
            return cast(AppConfig, config)
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


def get_automation_config(config: AppConfig) -> AutomationConfig:
    automation_config = cast(AutomationConfig, config.setdefault("automation", {}))
    automation_config["behaviour_toggles"] = get_behaviour_toggles_from_config(config)
    return automation_config


def get_behaviour_toggles_from_config(config: AppConfig) -> dict[BehaviourId, bool]:
    from behaviour.registry import get_default_behaviour_toggles

    automation_config = cast(dict[str, Any], config.get("automation", {}))
    raw_toggles = automation_config.get("behaviour_toggles") or {}

    default_toggles = get_default_behaviour_toggles()
    merged_toggles: dict[BehaviourId, bool] = default_toggles.copy()

    for behaviour_id in default_toggles:
        if behaviour_id in raw_toggles:
            merged_toggles[behaviour_id] = bool(raw_toggles[behaviour_id])

    return merged_toggles


def is_behaviour_enabled_in_config(config: AppConfig, behaviour_id: BehaviourId) -> bool:
    return get_behaviour_toggles_from_config(config).get(behaviour_id, True)


def clear_behaviour_cfg(config_file: str):
    """
    Removes behaviour key from config file
    """
    config: dict[str, Any] = load_config(config_file)
    if "behaviour" in config:
        config.pop("behaviour")
    save_config(config_file, config)
