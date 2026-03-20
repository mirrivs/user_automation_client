# Registry of all behaviour classes
from typing import Type

from behaviour.behaviour import BaseBehaviour
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
