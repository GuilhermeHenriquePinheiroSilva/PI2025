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

@router.post("/", response_model=EnterpriseResponse, status_code=status.HTTP_201_CREATED)
async def register_enterprise(enterprise: EnterpriseCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova empresa.
    """
    db_email = db.query(EmpresaORM).filter(EmpresaORM.email == enterprise.email).first()
    if db_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já registrado")
        
    db_cnpj = db.query(EmpresaORM).filter(EmpresaORM.cnpj == enterprise.cnpj).first()
    if db_cnpj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CNPJ já registrado")

    hashed_password = get_password_hash(enterprise.senha)

    new_enterprise = EmpresaORM(
        nome_fantasia=enterprise.nome_fantasia,
        cnpj=enterprise.cnpj,
        nome_admin_empresa=enterprise.nome_admin_empresa,
        cpf_adm=enterprise.cpf_adm,
        telefone=enterprise.telefone,
        email=enterprise.email,
        senha=hashed_password
    )
    db.add(new_enterprise)
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