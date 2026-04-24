from typing import Mapping

from lib.selenium.models import EmailClient, EmailClientUser


def build_email_client_user(
    user: Mapping[str, str],
    email_client_type: EmailClient,
    force_external_credentials: bool = False,
) -> EmailClientUser:
    """Create a normalized EmailClientUser from automation config values."""
    if force_external_credentials:
        email = user.get("external_email")
        password = user.get("external_password")
    else:
        email = user.get("internal_email")
        password = user.get("internal_password")

    if not email or not password:
        raise ValueError("Email client user must include both email and password")

    name = user.get("name")
    if not name:
        local_part = email.split("@", 1)[0]
        name = local_part.replace(".", " ").replace("_", " ").title()

    return {
        "name": name,
        "email": email,
        "password": password,
    }
