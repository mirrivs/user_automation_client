# Registry of all behaviour classes
from typing import Type

from behaviour.behaviour import BaseBehaviour
from behaviour.behaviours.attack_phishing import BehaviourAttackPhishing
from behaviour.behaviours.attack_ransomware import BehaviourAttackRansomware
from behaviour.behaviours.attack_reverse_shell import BehaviourAttackReverseShell
from behaviour.behaviours.procrastination import BehaviourProcrastination
from behaviour.behaviours.work_developer import BehaviourWorkDeveloper
from behaviour.behaviours.work_emails import BehaviourWorkEmails
from behaviour.behaviours.work_organization_web import BehaviourWorkOrganizationWeb
from behaviour.behaviours.work_word import BehaviourWorkWord

BEHAVIOURS: list[Type[BaseBehaviour]] = [
    BehaviourAttackPhishing,
    BehaviourAttackRansomware,
    BehaviourAttackReverseShell,
    BehaviourProcrastination,
    BehaviourWorkDeveloper,
    BehaviourWorkEmails,
    BehaviourWorkOrganizationWeb,
    BehaviourWorkWord,
]
