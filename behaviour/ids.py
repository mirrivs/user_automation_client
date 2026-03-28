from typing import Literal, TypeAlias

BehaviourId: TypeAlias = Literal[
    "attack_phishing",
    "attack_ransomware",
    "attack_reverse_shell",
    "procrastination",
    "work_developer",
    "work_document",
    "work_emails",
    "work_organization_web",
    "work_presentation",
    "work_spreadsheet",
]
