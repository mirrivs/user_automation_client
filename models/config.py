from typing import TypedDict

from models.email_client import EmailClient


class User(TypedDict):
    domain_email: str
    domain_password: str
    o365_email: str
    o365_password: str


class IdleCycle(TypedDict):
    procrastination_chance: float


class General(TypedDict):
    email_client: EmailClient
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