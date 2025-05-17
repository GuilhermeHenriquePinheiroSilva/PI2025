from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from app.enums.roles import Role

class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: EmailStr
    password: str
    role: Optional[Role] = Role.CUSTOMER

    @field_validator("role", mode="before")
    @classmethod
    def default_role_if_empty(cls, v):
        if v in (None, "", " "):
            return Role.CUSTOMER
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str


