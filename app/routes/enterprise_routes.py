# app/routes/enterprise_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash

# 1. Importe TODAS as classes necessárias do seu pacote de modelos
from app.models import (
    EnterpriseRegister, 
    EnterpriseRead, 
    EnterpriseLogin, 
    EnterpriseORM, 
    UserORM
)

from app.auth.jwt_handler import create_access_token
# Corrija o import do get_db para o caminho correto
from app.database.db_config import get_db
from app.enums.roles import Role

router = APIRouter(
    prefix="/enterprises",
    tags=["Enterprises"]
)

### ROTA DE CADASTRO (SIGNUP) ###
# 2. Use os nomes das classes diretamente (ex: EnterpriseRead)
@router.post(
    "/register", 
    response_model=EnterpriseRead, 
    status_code=status.HTTP_201_CREATED
)
# 3. E também aqui (ex: EnterpriseRegister)
def register_enterprise(enterprise: EnterpriseRegister, db: Session = Depends(get_db)):
    # Verifica se o e-mail já existe
    user_exists = db.query(UserORM).filter(UserORM.email == enterprise.email).first()
    enterprise_exists = db.query(EnterpriseORM).filter(EnterpriseORM.email == enterprise.email).first()
    if user_exists or enterprise_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está em uso."
        )

    # Verifica se o CNPJ já existe
    cnpj_exists = db.query(EnterpriseORM).filter(EnterpriseORM.cnpj == enterprise.cnpj).first()
    if cnpj_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este CNPJ já está cadastrado."
        )

    # Cria o hash da senha
    hashed_password = generate_password_hash(enterprise.password)

    # Cria a instância do ORM para salvar no banco
    db_enterprise = EnterpriseORM(
        username=enterprise.username,
        email=enterprise.email,
        password=hashed_password,
        cnpj=enterprise.cnpj,
        role=Role.ENTERPRISE
    )

    db.add(db_enterprise)
    db.commit()
    db.refresh(db_enterprise)
    return db_enterprise

### ROTA DE LOGIN ###
@router.post("/login")
def login_enterprise(enterprise: EnterpriseLogin, db: Session = Depends(get_db)):
    db_enterprise = db.query(EnterpriseORM).filter(EnterpriseORM.email == enterprise.email).first()

    if not db_enterprise or not check_password_hash(db_enterprise.password, enterprise.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )

    # Cria o token
    token_data = {
        "sub": db_enterprise.email,
        "role": db_enterprise.role.value
    }
    token = create_access_token(data=token_data)

    return {
        "access_token": token,
        "token_type": "bearer",
        "enterprise": {
            "username": db_enterprise.username,
            "email": db_enterprise.email,
            "role": db_enterprise.role.value
        }
    }