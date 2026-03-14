# Registry of all behaviour classes
from typing import Type

from behaviour.behaviour import BaseBehaviour
from behaviour.behaviours.procrastination import BehaviourProcrastination

BEHAVIOURS: list[Type[BaseBehaviour]] = [
    # BehaviourAttackPhishing,
    # BehaviourAttackRansomware,
    # BehaviourAttackReverseShell,
    BehaviourProcrastination,
    # BehaviourTest,
    # BehaviourWorkDeveloper,
    # BehaviourWorkEmails,
    # BehaviourWorkOrganizationWeb,
    # BehaviourWorkWord,
    # BehaviourWorkExcel,
    # BehaviourWorkPowerpoint,
]
