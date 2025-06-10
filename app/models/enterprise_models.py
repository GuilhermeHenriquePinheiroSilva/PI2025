from pydantic import BaseModel, EmailStr
from typing import Optional
from app.enums.roles import Role 

class EnterpriseRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    cnpj: str

class EnterpriseLogin(BaseModel):
    email: EmailStr
    password: str

class EnterpriseRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: Role
    cnpj: str

    class Config:
        from_attributes = True