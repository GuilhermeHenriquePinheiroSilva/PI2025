from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash

# CORREÇÃO: Importando 'User' (como UserSchema) e 'UserLogin' do seu arquivo de modelos
from app.models.user_models import User as UserSchema, UserLogin
from app.models.user_orm import UserORM

# Usando o seu handler JWT original
from app.auth.jwt_handler import create_access_token
from app.database.db_config import get_db

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register")
async def register_user(user: UserSchema, db: Session = Depends(get_db)):
    """
    Registra um novo usuário usando o modelo 'User' existente.
    """
    db_user = db.query(UserORM).filter(UserORM.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já registrado")

    # Usando werkzeug, conforme seu padrão original
    hashed_password = generate_password_hash(user.password)

    new_user = UserORM(
        username=user.username,
        email=user.email,
        password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # Retornando uma mensagem simples, como no seu padrão original
    return {"message": "Usuário registrado com sucesso"}

@router.post("/login")
async def login_user(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    Realiza o login do usuário e retorna o token e os dados do usuário.
    """
    user = db.query(UserORM).filter(UserORM.email == user_login.email).first()
    
    # Usando werkzeug e tratando o caso de usuário não encontrado
    if not user or not check_password_hash(user.password, user_login.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Convertendo o Enum para string para o token e a resposta
    token_data = {"sub": user.email, "role": user.role.name}
    access_token = create_access_token(token_data)
    
    # Retornando a resposta completa que o frontend espera
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "email": user.email,
            "role": user.role.name 
        }
    }