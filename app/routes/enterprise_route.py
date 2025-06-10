from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import empresa_models, empresa_orm, user_orm

from app.auth.jwt_handler import create_access_token
from app.database.db_config import get_db 
from app.enums.roles import Role 

router = APIRouter(
    prefix="/empresas",
    tags=["Empresas"]
)

### ROTA DE CADASTRO (SIGNUP) ###
@router.post(
    "/register", 
    response_model=empresa_models.EmpresaRead, 
    status_code=status.HTTP_201_CREATED
)
def register_empresa(empresa: empresa_models.EmpresaCreate, db: Session = Depends(get_db)):
    """
    Cadastra uma nova empresa no sistema.
    - Verifica se o e-mail ou CNPJ já existem.
    - Armazena a senha de forma segura (hash).
    - Atribui o papel (role) de 'COMPANY'.
    """
    # Verifica se o e-mail já existe na tabela de usuários ou de empresas
    user_exists = db.query(user_orm.UserORM).filter(user_orm.UserORM.email == empresa.email).first()
    empresa_exists = db.query(empresa_orm.EmpresaORM).filter(empresa_orm.EmpresaORM.email == empresa.email).first()
    if user_exists or empresa_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está em uso."
        )

    # Verifica se o CNPJ já existe
    cnpj_exists = db.query(empresa_orm.EmpresaORM).filter(empresa_orm.EmpresaORM.cnpj == empresa.cnpj).first()
    if cnpj_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este CNPJ já está cadastrado."
        )

    # Cria o hash da senha usando werkzeug.security
    hashed_password = generate_password_hash(empresa.password)

    # Cria a instância do ORM para salvar no banco
    db_empresa = empresa_orm.EmpresaORM(
        username=empresa.username,
        email=empresa.email,
        password=hashed_password,  # Salva o hash, não a senha pura
        cnpj=empresa.cnpj,
        role=Role.COMPANY  # Define o papel fixo para empresa
    )

    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)

    return db_empresa

### ROTA DE LOGIN ###
@router.post("/login")
def login_empresa(empresa: empresa_models.EmpresaLogin, db: Session = Depends(get_db)):
    """
    Autentica uma empresa e retorna um token de acesso JWT.
    """
    # Busca a empresa pelo e-mail
    db_empresa = db.query(empresa_orm.EmpresaORM).filter(empresa_orm.EmpresaORM.email == empresa.email).first()

    # Verifica se a empresa existe e se a senha está correta
    if not db_empresa or not check_password_hash(db_empresa.password, empresa.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )

    # Cria o token JWT com os dados da empresa
    token_data = {
        "sub": db_empresa.email,
        "role": db_empresa.role.value # Usa .value para obter o valor do Enum (ex: "COMPANY")
    }
    token = create_access_token(data=token_data)

    # Retorna o token e os dados básicos da empresa
    return {
        "access_token": token,
        "token_type": "bearer",
        "empresa": {
            "username": db_empresa.username,
            "email": db_empresa.email,
            "role": db_empresa.role.value
        }
    }