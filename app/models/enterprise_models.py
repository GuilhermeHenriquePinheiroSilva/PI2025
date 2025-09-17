from app.enums.roles import Role
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

# Modelo base para a empresa (representação completa no sistema)
class Enterprise(BaseModel):
    id: Optional[int] = None
    nome_fantasia: str
    cnpj: str
    nome_admin_empresa: str
    cpf_adm: str
    telefone: str
    email: EmailStr
    role: Optional[Role] = Role.CUSTOMER
    senha: str
    creation_date: Optional[datetime] = None

    @field_validator("role", mode="before")
    @classmethod
    def default_role_if_empty(cls, v):
        if v in (None, "", " "):
            return Role.ENTERPRISE
        return v

    class Config:
        from_attributes = True

# Modelo para o registro de uma nova empresa (senha é obrigatória)
class EnterpriseCreate(BaseModel):
    nome_fantasia: str
    cnpj: str
    nome_admin_empresa: str
    cpf_adm: str
    telefone: str
    email: EmailStr
    senha: str

# Modelo para o login da empresa
class EnterpriseLogin(BaseModel):
    email: EmailStr
    senha: str

# Modelo para a resposta da API (não retorna a senha)
class EnterpriseResponse(BaseModel):
    id: int
    nome_fantasia: str
    cnpj: str
    nome_admin_empresa: str
    cpf_adm: str
    telefone: str
    email: EmailStr
    creation_date: datetime

    class Config:
        from_attributes = True