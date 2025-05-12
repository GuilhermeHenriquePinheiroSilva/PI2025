from pydantic import BaseModel, EmailStr
from typing import Optional
from app.enums.roles import Role
from pydantic import validator

class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: EmailStr
    password: str
    role: Optional[Role] = Role.CUSTOMER

    @validator("role", pre=True, always=True)
    def default_role_if_empty(cls, v):
        if v in (None, "", " "):
            return Role.CUSTOMER
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str


