from app.enums.roles import Role
from app.models.user_orm import UserORM
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.db_config import get_db
from app.models.enterprise_orm import EmpresaORM
from app.models.enterprise_models import EnterpriseCreate, EnterpriseResponse
from app.security import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(
    prefix="/enterprise",
    tags=["Enterprise"]
)

@router.post("/register", response_model=EnterpriseResponse, status_code=status.HTTP_201_CREATED)
async def register_enterprise(
    enterprise: EnterpriseCreate, 
    db: Session = Depends(get_db), 
    current_user: UserORM = Depends(get_current_user)
):
    # Verifica se o CNPJ ou CPF já existem
    if db.query(EmpresaORM).filter(EmpresaORM.cnpj == enterprise.cnpj).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CNPJ já registrado")
    if db.query(EmpresaORM).filter(EmpresaORM.cpf_adm == enterprise.cpf_adm).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF do administrador já registrado")
    
    # Verifica se o usuário já possui uma empresa
    if current_user.enterprise_details:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário já possui uma empresa cadastrada")

    # Cria a nova empresa
    new_enterprise = EmpresaORM(
        **enterprise.model_dump(),
        user_id=current_user.id
    )
    db.add(new_enterprise)

    # Atualiza a role do usuário
    current_user.role = Role.ENTERPRISE
    db.add(current_user)

    db.commit()
    db.refresh(new_enterprise)
    
    return new_enterprise

@router.get("/", response_model=List[EnterpriseResponse])
async def get_all_enterprises(db: Session = Depends(get_db)):
    """
    Retorna uma lista de todas as empresas cadastradas.
    """
    enterprises = db.query(EmpresaORM).all()
    return enterprises

@router.get("/{enterprise_id}", response_model=EnterpriseResponse)
async def get_enterprise_by_id(enterprise_id: int, db: Session = Depends(get_db)):
    """
    Retorna uma empresa específica por ID.
    """
    enterprise = db.query(EmpresaORM).filter(EmpresaORM.id == enterprise_id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")
    return enterprise

@router.put("/{enterprise_id}", response_model=EnterpriseResponse)
async def update_enterprise(
    enterprise_id: int,
    enterprise_update: EnterpriseCreate,
    db: Session = Depends(get_db),
):
    """
    Atualiza uma empresa por ID.
    """
    db_enterprise = db.query(EmpresaORM).filter(EmpresaORM.id == enterprise_id).first()
    if not db_enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")

    if enterprise_update.senha:
        hashed_password = get_password_hash(enterprise_update.senha)
        db_enterprise.senha = hashed_password

    for field, value in enterprise_update.model_dump(exclude_unset=True).items():
        setattr(db_enterprise, field, value)

    db.commit()
    db.refresh(db_enterprise)
    return db_enterprise

@router.delete("/{enterprise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_enterprise(
    enterprise_id: int,
    db: Session = Depends(get_db),
):
    """
    Deleta uma empresa por ID.
    """
    db_enterprise = db.query(EmpresaORM).filter(EmpresaORM.id == enterprise_id).first()
    if not db_enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")

    db.delete(db_enterprise)
    db.commit()
    return {"message": "Empresa excluída com sucesso"}