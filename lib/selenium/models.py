from enum import Enum
from typing import TypedDict


class EmailClient(Enum):
    OWA = "owa"
    ROUNDCUBE = "roundcube"
    O365 = "o365"


class EmailClientUser(TypedDict):
    name: str
    email: str
    password: str
