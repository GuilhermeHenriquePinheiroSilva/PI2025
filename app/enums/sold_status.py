from enum import Enum

class SoldStatus(str, Enum):
    VALID = "VALID"
    USED = "USED"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"