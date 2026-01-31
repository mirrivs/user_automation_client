from enum import Enum
from typing import TypedDict


class MailClient(Enum):
    OWA = "owa"
    ROUNDCUBE = "roundcube"
    O365 = "o365"


class User(TypedDict):
    email: str
    password: str


class IdleCycle(TypedDict):
    procrastination_chance: float


class General(TypedDict):
    mail_client: MailClient
    user: User
    is_conversation_starter: bool
    organization_mail_server_url: str
    organization_web_url: str
    archive_path: str


class AttackRansomware(TypedDict):
    malicious_email_subject: str


class AttackPhishing(TypedDict):
    malicious_email_subject: str


class Procrastination(TypedDict):
    procrastination_preference: float
    procrastination_max_time: float
    procrastination_min_time: float


class WorkEmails(TypedDict):
    email_receivers: list[str]


class BehavioursConfigs(TypedDict):
    procrastination: Procrastination
    work_emails: WorkEmails
    attack_phishing: AttackPhishing


class AutomationConfig(TypedDict):
    general: General
    idle_cycle: IdleCycle
    behaviours: BehavioursConfigs


class App(TypedDict):
    user_automation_server_http: str
    user_automation_server_socket: str


class AppConfig(TypedDict):
    app: App
    automation: AutomationConfig