# app/routes/auth_routes.py

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import os

# Importe os Pydantic models (Schemas)
from app.models.user_models import User as UserSchema, UserLogin

# Importe o modelo ORM
from app.models.user_orm import UserORM

# Funções de autenticação e email
from app.auth.jwt_handler import create_email_verification_token, verify_email_verification_token
from app.services.email_service import send_verification_email
from app.security import get_password_hash, verify_password, create_access_token, get_current_user
from app.database.db_config import get_db

router = APIRouter(
    prefix="/auth", 
    tags=["Authentication"]
)

# Pydantic models para as requisições de redefinição de senha
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserSchema, db: Session = Depends(get_db)):
    db_user = db.query(UserORM).filter(UserORM.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já registrado")

    hashed_password = get_password_hash(user.password)

    new_user = UserORM(
        username=user.username,
        email=user.email,
        password=hashed_password,
        role=user.role 
    )

    # 1. Salva o usuário no banco para obter uma ID
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    try:
        # 2. Cria o token de verificação com a ID do usuário
        token = create_email_verification_token(str(new_user.id))
        
        # 3. Envia o email
        send_verification_email(new_user.email, token)

    except Exception as e:
        print(f"\n!!! ALERTA: Usuário {new_user.email} foi registrado, mas o email de verificação falhou. Erro: {e}\n")

    return {"message": "Usuário registrado com sucesso. Por favor, verifique seu email."}


@router.post("/login")
async def login_user(user_login: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(UserORM).filter(UserORM.email == user_login.email).first()
    
    if not db_user or not verify_password(user_login.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Email ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {"sub": db_user.email, "role": db_user.role.name}
    token = create_access_token(token_data)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "role": db_user.role.name
        }
    }


@router.get("/verify-email")
async def verify_email(token: str = Query(...), db: Session = Depends(get_db)):
    user_id_str = verify_email_verification_token(token)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de ID de usuário inválido no token")

    user = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    # --- CORREÇÃO AQUI ---
    if user.emailverified: # Trocado de email_verified para emailverified
        return {"message": "Email já foi verificado anteriormente."}

    # --- E CORREÇÃO AQUI ---
    user.emailverified = True # Trocado de email_verified para emailverified
    db.commit()

    return {"message": "Email verificado com sucesso!"}


@router.get("/me")
async def read_users_me(current_user: UserORM = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.name
    }