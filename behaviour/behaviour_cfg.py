from behaviour.models.exceptions import BehaviourException
from app_config import automation_config


def get_behaviour_cfg(behaviour_id: str, required: bool = False) -> dict:
    """
    Retrieve behaviour configuration from main config.

    Args:
        behaviour_id: Id of the behaviour to get config for
        required: If True, raises BehaviourException when config not found

    Returns:
        Behaviour configuration dict, or empty dict if not found and not required
    """
    behaviour_cfg = automation_config.get("behaviours", {}).get(behaviour_id, {})
    if not behaviour_cfg and required:
        raise BehaviourException(f"Configuration for task '{behaviour_id}' not found")
    return behaviour_cfg
