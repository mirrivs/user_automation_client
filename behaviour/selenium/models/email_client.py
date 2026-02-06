from enum import Enum


class EmailClient(Enum):
    OWA = "owa"
    ROUNDCUBE = "roundcube"
    O365 = "o365"
