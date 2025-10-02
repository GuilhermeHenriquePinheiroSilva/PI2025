from datetime import timedelta
import os
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

# Importe os Pydantic models (Schemas)
from app.auth.jwt_handler import decode_access_token
from app.models.user_models import User as UserSchema, UserLogin

# Importe o modelo ORM
from app.models.user_orm import UserORM

# Importe as novas funções de segurança e o get_db centralizado
from app.security import create_access_token, get_current_user
from app.database.db_config import get_db
from app.services.email_service import send_email_with_template
from werkzeug.security import generate_password_hash

# É uma boa prática agrupar rotas relacionadas com um prefixo e uma tag
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

# @router.post("/register")
# async def register_user(user: UserSchema, db: Session = Depends(get_db)):
#     db_user = db.query(UserORM).filter(UserORM.email == user.email).first()
#     if db_user:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já registrado")

#     hashed_password = get_password_hash(user.password)

#     new_user = UserORM(
#         username=user.username,
#         email=user.email,
#         password=hashed_password,
#         role=user.role 
#     )
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return {"message": "Usuário registrado com sucesso"}

# @router.post("/login")
# async def login_user(user_login: UserLogin, db: Session = Depends(get_db)):
#     db_user = db.query(UserORM).filter(UserORM.email == user_login.email).first()
    
#     if not db_user or not verify_password(user_login.password, db_user.password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, 
#             detail="Email ou senha inválidos",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     token_data = {"sub": db_user.email, "role": db_user.role.name}
#     token = create_access_token(token_data)
    
#     return {
#         "access_token": token,
#         "token_type": "bearer",
#         "user": {
#             "id": db_user.id,
#             "username": db_user.username,
#             "email": db_user.email,
#             "role": db_user.role.name
#         }
#     }

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(UserORM).filter(UserORM.email == data.email).first()
    if not user:
        # Por segurança, não confirme se o e-mail existe.
        # A mensagem de sucesso é retornada de qualquer forma.
        return {"message": "Se um usuário com este email existir, um link de redefinição foi enviado."}

    # Gera um token de curta duração para a redefinição de senha
    token = create_access_token({"sub": user.email}, expires_delta=timedelta(minutes=15))

    # Lógica para escolher a URL base (localhost ou produção)
    app_env = os.getenv("APP_ENV")
    if app_env == "development":
        base_url = "http://localhost:4200"
    else:
        base_url = os.getenv("FRONTEND_URL")
        
    reset_link = f"{base_url}/reset-password?token={token}"

    # Envia o e-mail em segundo plano
    background_tasks.add_task(
        send_email_with_template,
        subject="Redefinição de Senha - GoGift",
        recipients=[user.email],
        template_name="reset_password.html",
        template_body={"reset_link": reset_link}
    )

    return {"message": "Se um usuário com este email existir, um link de redefinição foi enviado."}

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    payload = decode_access_token(data.token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token inválido ou expirado"
        )

    email = payload.get("sub")
    user = db.query(UserORM).filter(UserORM.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuário não encontrado"
        )

    # Gera o hash da nova senha e a atualiza no banco
    hashed_password = generate_password_hash(data.new_password)
    user.password = hashed_password
    db.commit()
    
    return {"message": "Senha redefinida com sucesso"}

@router.get("/me")
async def read_users_me(current_user: UserORM = Depends(get_current_user)):
    # Rota protegida que retorna os dados do usuário logado
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.name
    }
