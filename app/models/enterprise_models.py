from app.enums.roles import Role
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum # Importar Enum para o status

# Adicionado para definir os status possíveis da empresa
class EnterpriseStatus(str, Enum):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'

# --- NOVO MODELO ADICIONADO ---
# Modelo para receber o motivo da rejeição no corpo da requisição
class EnterpriseRejection(BaseModel):
    rejection_reason: str

# Modelo para a criação de uma nova empresa, associado a um usuário existente
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

    # --- CAMPOS ADICIONADOS ---
    # Adiciona o status e o motivo da rejeição (opcional) à resposta da API
    status: EnterpriseStatus
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True