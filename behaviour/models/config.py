from typing import TypedDict


class AttackPhishingCfg(TypedDict):
    malicious_email_subject: str


class AttackRansomwareCfg(TypedDict):
    malicious_email_subject: str


class AttackReverseShellCfg(TypedDict):
    malicious_email_subject: str


class WorkEmailsCfg(TypedDict):
    malicious_email_subject: str


class ProcrastinationCfg(TypedDict):
    max_duration: int
    min_duration: int
    preference: dict[str, float]
