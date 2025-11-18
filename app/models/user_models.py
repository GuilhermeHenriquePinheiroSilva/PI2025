from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from app.enums.roles import Role
from app.enums.tags import Tag 
import re

class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: EmailStr
    password: str
    role: Optional[Role] = Role.CUSTOMER
    tags: Optional[Tag] = None 
    account_type: str # 'person' ou 'enterprise'
    cpf: Optional[str] = None
    cnpj: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_validation(cls, v):
        """Valida que a senha atende aos critérios de segurança."""
        if len(v) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
        if not re.search(r"[a-z]", v):
            raise ValueError("A senha deve conter pelo menos uma letra minúscula.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("A senha deve conter pelo menos uma letra maiúscula.")
        if not re.search(r"[0-9]", v):
            raise ValueError("A senha deve conter pelo menos um número.")
        # O conjunto de caracteres especiais pode ser ajustado conforme sua necessidade
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("A senha deve conter pelo menos um caractere especial.")
        return v

    @field_validator("role", mode="before")
    @classmethod
    def default_role_if_empty(cls, v):
        if v in (None, "", " "):
            return Role.CUSTOMER
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str