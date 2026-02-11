from typing import Type, TypeVar, overload

from app_config import automation_config
from behaviour.models.exceptions import BehaviourException

T = TypeVar("T")


@overload
def get_behaviour_cfg(behaviour_id: str, cfg_type: Type[T], required: bool = False) -> T: ...


@overload
def get_behaviour_cfg(behaviour_id: str, *, required: bool = False) -> dict: ...


def get_behaviour_cfg(behaviour_id: str, cfg_type: type = dict, required: bool = False) -> dict:  # type: ignore[overload-impl]
    """
    Retrieve behaviour configuration from main config.

    Args:
        behaviour_id: Id of the behaviour to get config for
        cfg_type: Type hint for the returned config (used for type checking only)
        required: If True, raises BehaviourException when config not found

    Returns:
        Behaviour configuration dict, or empty dict if not found and not required
    """
    behaviour_cfg = automation_config.get("behaviours", {}).get(behaviour_id, {})
    if not behaviour_cfg and required:
        raise BehaviourException(f"Configuration for task '{behaviour_id}' not found")
    return behaviour_cfg
