from enum import Enum

class Role(str, Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"
    ENTERPRISE = "ENTERPRISE"