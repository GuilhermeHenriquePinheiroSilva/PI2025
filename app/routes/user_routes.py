from datetime import timedelta
import os
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
import re 

from app.auth.jwt_handler import decode_access_token
from app.models.user_models import User as UserSchema, UserLogin

from app.models.user_orm import UserORM

from app.security import create_access_token, get_current_user

from app.database.db_config import get_db
from app.services.email_service import send_email_with_template
from werkzeug.security import generate_password_hash

router = APIRouter(
    prefix="/auth", 
    tags=["Authentication"]
)

class UserDetailsResponse(BaseModel):
    username: str
    email: str
    account_type: str
    cpf: str | None = None
    cnpj: str | None = None
    role: str # Enviamos a role como string

    class Config:
        from_attributes = True

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_validation(cls, v):
        """Valida que a nova senha atende aos critérios de segurança."""
        if len(v) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
        if not re.search(r"[a-z]", v):
            raise ValueError("A senha deve conter pelo menos uma letra minúscula.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("A senha deve conter pelo menos uma letra maiúscula.")
        if not re.search(r"[0-9]", v):
            raise ValueError("A senha deve conter pelo menos um número.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("A senha deve conter pelo menos um caractere especial.")
        return v

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(UserORM).filter(UserORM.email == data.email).first()
    if not user:
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

@router.get("/me", response_model=UserDetailsResponse) # 1. Adicionamos o response_model
async def read_users_me(current_user: UserORM = Depends(get_current_user)):
    # 2. Usamos o Pydantic model 'UserDetailsResponse' para validar
    #    e formatar a saída.
    response_data = UserDetailsResponse.model_validate(current_user)
    
    # 3. Convertemos o Enum da Role para String (ex: Role.CUSTOMER -> "CUSTOMER")
    response_data.role = current_user.role.name 

    return response_data