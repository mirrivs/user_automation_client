# Registry of all behaviour classes
from typing import Type

from behaviour.behaviour import BaseBehaviour
from behaviour.ids import BehaviourId
from behaviours.attack_phishing import BehaviourAttackPhishing
from behaviours.attack_ransomware import BehaviourAttackRansomware
from behaviours.attack_reverse_shell import BehaviourAttackReverseShell
from behaviours.procrastination import BehaviourProcrastination
from behaviours.work_developer import BehaviourWorkDeveloper
from behaviours.work_document import BehaviourWorkDocument
from behaviours.work_emails import BehaviourWorkEmails
from behaviours.work_organization_web import BehaviourWorkOrganizationWeb
from behaviours.work_presentation import BehaviourWorkPresentation
from behaviours.work_spreadsheet import BehaviourWorkSpreadsheet

BEHAVIOURS: list[Type[BaseBehaviour]] = [
    BehaviourAttackPhishing,
    BehaviourAttackRansomware,
    BehaviourAttackReverseShell,
    BehaviourProcrastination,
    # BehaviourTest,
    BehaviourWorkDeveloper,
    BehaviourWorkEmails,
    BehaviourWorkOrganizationWeb,
    BehaviourWorkDocument,
    BehaviourWorkSpreadsheet,
    BehaviourWorkPresentation,
]


def get_registered_behaviour_ids(
    behaviour_classes: list[Type[BaseBehaviour]] = BEHAVIOURS,
) -> list[BehaviourId]:
    return [behaviour_class.id for behaviour_class in behaviour_classes]



def get_default_behaviour_toggles(
    behaviour_classes: list[Type[BaseBehaviour]] = BEHAVIOURS,
) -> dict[BehaviourId, bool]:
    return {behaviour_id: True for behaviour_id in get_registered_behaviour_ids(behaviour_classes)}



def validate_behaviour_registry(
    behaviour_classes: list[Type[BaseBehaviour]] = BEHAVIOURS,
) -> None:
    seen: set[BehaviourId] = set()
    duplicate_ids: set[BehaviourId] = set()

    for behaviour_class in behaviour_classes:
        behaviour_id = behaviour_class.id
        if behaviour_id in seen:
            duplicate_ids.add(behaviour_id)
            continue
        seen.add(behaviour_id)

    if duplicate_ids:
        duplicates = ", ".join(sorted(duplicate_ids))
        raise ValueError(f"Duplicate behaviour IDs detected in registry: {duplicates}")
