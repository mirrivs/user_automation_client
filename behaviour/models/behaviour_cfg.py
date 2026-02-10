from typing import TypedDict


class AttackReverseShellCfg(TypedDict):
    malicious_email_subject: str


class ProcrastinationCfg(TypedDict):
    max_duration: float
    min_duration: float
    preference: dict[str, float]
