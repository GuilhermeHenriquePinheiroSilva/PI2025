from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import enterprise_models, enterprise_orm, user_orm

from app.auth.jwt_handler import create_access_token
from app.database.db_config import get_db 
from app.enums.roles import Role 

router = APIRouter(
    prefix="/enterprises",
    tags=["Enterprises"]
)

### ROTA DE CADASTRO (SIGNUP) ###
@router.post(
    "/register", 
    response_model=enterprise_models.EnterpriseRead, 
    status_code=status.HTTP_201_CREATED
)
def register_enterprise(enterprise: enterprise_models.EnterpriseCreate, db: Session = Depends(get_db)):
    """
    Cadastra uma nova enterprise no sistema.
    - Verifica se o e-mail ou CNPJ já existem.
    - Armazena a senha de forma segura (hash).
    - Atribui o papel (role) de 'COMPANY'.
    """
    # Verifica se o e-mail já existe na tabela de usuários ou de enterprises
    user_exists = db.query(user_orm.UserORM).filter(user_orm.UserORM.email == enterprise.email).first()
    enterprise_exists = db.query(enterprise_orm.EnterpriseORM).filter(enterprise_orm.EnterpriseORM.email == enterprise.email).first()
    if user_exists or enterprise_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está em uso."
        )

    # Verifica se o CNPJ já existe
    cnpj_exists = db.query(enterprise_orm.EnterpriseORM).filter(enterprise_orm.EnterpriseORM.cnpj == enterprise.cnpj).first()
    if cnpj_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este CNPJ já está cadastrado."
        )

    # Cria o hash da senha usando werkzeug.security
    hashed_password = generate_password_hash(enterprise.password)

    # Cria a instância do ORM para salvar no banco
    db_enterprise = enterprise_orm.EnterpriseORM(
        username=enterprise.username,
        email=enterprise.email,
        password=hashed_password,  # Salva o hash, não a senha pura
        cnpj=enterprise.cnpj,
        role=Role.COMPANY  # Define o papel fixo para enterprise
    )

    db.add(db_enterprise)
    db.commit()
    db.refresh(db_enterprise)

    return db_enterprise

### ROTA DE LOGIN ###
@router.post("/login")
def login_enterprise(enterprise: enterprise_models.EnterpriseLogin, db: Session = Depends(get_db)):
    """
    Autentica uma enterprise e retorna um token de acesso JWT.
    """
    # Busca a enterprise pelo e-mail
    db_enterprise = db.query(enterprise_orm.EnterpriseORM).filter(enterprise_orm.EnterpriseORM.email == enterprise.email).first()

    # Verifica se a enterprise existe e se a senha está correta
    if not db_enterprise or not check_password_hash(db_enterprise.password, enterprise.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )

    # Cria o token JWT com os dados da enterprise
    token_data = {
        "sub": db_enterprise.email,
        "role": db_enterprise.role.value # Usa .value para obter o valor do Enum (ex: "COMPANY")
    }
    token = create_access_token(data=token_data)

    # Retorna o token e os dados básicos da enterprise
    return {
        "access_token": token,
        "token_type": "bearer",
        "enterprise": {
            "username": db_enterprise.username,
            "email": db_enterprise.email,
            "role": db_enterprise.role.value
        }
    }