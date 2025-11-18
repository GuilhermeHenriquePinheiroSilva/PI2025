from datetime import timedelta
import os
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
from app.enums.roles import Role
from app.models.user_models import User as UserSchema, UserLogin
from app.models.user_orm import UserORM

from app.auth.jwt_handler import create_access_token, decode_access_token
from app.database.db_config import get_db
from app.services.email_service import send_email_with_template


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register")
async def register_user(user: UserSchema, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    db_user = db.query(UserORM).filter(UserORM.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já registrado")
    
    if user.account_type == 'person':
        if not user.cpf:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF é obrigatório para pessoa física")
        db_cpf = db.query(UserORM).filter(UserORM.cpf == user.cpf).first()
        if db_cpf:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF já registrado")
        user.cnpj = None # Garante que CNPJ é nulo
    
    elif user.account_type == 'enterprise':
        if not user.cnpj:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CNPJ é obrigatório para pessoa jurídica")
        db_cnpj = db.query(UserORM).filter(UserORM.cnpj == user.cnpj).first()
        if db_cnpj:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CNPJ já registrado")
        user.cpf = None # Garante que CPF é nulo
    
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de conta inválido ('person' ou 'enterprise' esperado)")
    # --- FIM DA LÓGICA ---

    hashed_password = generate_password_hash(user.password)

    new_user = UserORM(
        username=user.username,
        email=user.email,
        password=hashed_password,
        role=Role.CUSTOMER, # <--- MUDANÇA CRUCIAL: Todos se registram como CUSTOMER
        is_active=False,
        
        # --- CAMPOS ADICIONADOS ---
        account_type=user.account_type,
        cpf=user.cpf,
        cnpj=user.cnpj
        # --- FIM DOS CAMPOS ---
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.email}, expires_delta=timedelta(hours=24))

    app_env = os.getenv("APP_ENV")
    
    if app_env == "development":
        base_url = "http://localhost:4200"
    else:
        base_url = os.getenv("FRONTEND_URL")

   
    verification_link = f"{base_url}/verify-email?token={token}"
    

    # Envie o e-mail em segundo plano
    background_tasks.add_task(
        send_email_with_template,
        subject="Verifique seu e-mail - GoGift",
        recipients=[new_user.email],
        template_name="email_verification.html",
        template_body={"verification_link": verification_link}
    )

    return {"message": "Usuário registrado com sucesso. Um e-mail de verificação foi enviado."}

@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")

    email = payload["sub"]
    user = db.query(UserORM).filter(UserORM.email == email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    if user.is_active:
        return {"message": "Conta já ativada."}

    user.is_active = True
    db.commit()

    return {"message": "E-mail verificado com sucesso! Você já pode fazer login."}


@router.post("/login")
async def login_user(user_login: UserLogin, db: Session = Depends(get_db)):
    user = db.query(UserORM).filter(UserORM.email == user_login.email).first()

    if not user or not check_password_hash(user.password, user_login.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # VERIFICA SE A CONTA ESTÁ ATIVA
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Por favor, verifique seu e-mail para ativar sua conta."
        )

    role_value = user.role.name.lower()
    token_data = {"sub": user.email, "role": role_value}
    access_token = create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            # "email": user.email,
            "role": user.role.name 
        }
    }