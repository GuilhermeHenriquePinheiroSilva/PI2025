from app.enums.roles import Role
from app.models.user_orm import UserORM
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.db_config import get_db
from app.models.enterprise_orm import EmpresaORM
from app.models.enterprise_models import EnterpriseCreate, EnterpriseLogin, EnterpriseResponse
from app.security import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(
    prefix="/enterprise",
    tags=["Enterprise"]
)

@router.post("/register", response_model=EnterpriseResponse, status_code=status.HTTP_201_CREATED)
async def register_enterprise(enterprise: EnterpriseCreate, db: Session = Depends(get_db)):
    # Verifica se o email, CNPJ ou CPF já existem
    if db.query(UserORM).filter(UserORM.email == enterprise.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já registrado")
    if db.query(EmpresaORM).filter(EmpresaORM.cnpj == enterprise.cnpj).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CNPJ já registrado")
    if db.query(EmpresaORM).filter(EmpresaORM.cpf_adm == enterprise.cpf_adm).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF do administrador já registrado")

    hashed_password = get_password_hash(enterprise.senha)

    # 1. Cria o registro de usuário
    new_user = UserORM(
        username=enterprise.nome_fantasia,  # Usando nome fantasia como username
        email=enterprise.email,
        password=hashed_password,
        role=Role.ENTERPRISE
    )
    db.add(new_user)
    db.flush() # Usa flush para obter o ID do novo usuário antes do commit

    # 2. Cria o registro da empresa, associando ao usuário recém-criado
    new_enterprise = EmpresaORM(
        nome_fantasia=enterprise.nome_fantasia,
        cnpj=enterprise.cnpj,
        nome_admin_empresa=enterprise.nome_admin_empresa,
        cpf_adm=enterprise.cpf_adm,
        telefone=enterprise.telefone,
        email=enterprise.email,
        senha=hashed_password,
        role=Role.ENTERPRISE.value,
        user_id=new_user.id # Associa o ID do usuário
    )
    db.add(new_enterprise)
    db.commit()
    db.refresh(new_enterprise)
    
    return new_enterprise

@router.post("/login")
async def login_enterprise(enterprise_credentials: EnterpriseLogin, db: Session = Depends(get_db)):
    # A lógica de login agora busca na tabela de usuários
    user = db.query(UserORM).filter(UserORM.email == enterprise_credentials.email).first()
    
    if not user or not verify_password(enterprise_credentials.senha, user.password) or user.role != Role.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": user.email, "role": user.role.value})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": { "username": user.username, "email": user.email, "role": user.role.value }
    }

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