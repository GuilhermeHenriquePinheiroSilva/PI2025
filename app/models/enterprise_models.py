from pydantic import BaseModel, EmailStr
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
    senha: str
    creation_date: Optional[datetime] = None

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