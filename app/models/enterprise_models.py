from app.enums.roles import Role
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Modelo para a criação de uma nova empresa, associada a um usuário existente
class EnterpriseCreate(BaseModel):
    nome_fantasia: str
    cnpj: str
    nome_admin_empresa: str
    cpf_adm: str
    telefone: str

# Modelo para a resposta da API (não retorna dados sensíveis)
class EnterpriseResponse(BaseModel):
    id: int
    nome_fantasia: str
    cnpj: str
    nome_admin_empresa: str
    cpf_adm: str
    telefone: str
    creation_date: datetime
    user_id: int

    class Config:
        from_attributes = True