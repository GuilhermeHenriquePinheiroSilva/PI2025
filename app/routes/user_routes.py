from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user_models import User, UserLogin
from app.models.user_orm import UserORM
from app.auth.jwt_handler import create_access_token, verify_token
from app.database.db_config import SessionLocal
from pydantic import BaseModel, EmailStr


router = APIRouter()

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# Dependência para obter uma sessão de banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
async def register_user(user: User, db: Session = Depends(get_db)):
    db_user = db.query(UserORM).filter(UserORM.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já registrado")

    hashed_password = generate_password_hash(user.password)

    role = user.role or Role.CUSTOMER

    new_user = UserORM(
        username=user.username,
        email=user.email,
        password=hashed_password,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Usuário registrado com sucesso", "user_id": new_user.id}

@router.post("/login")
async def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(UserORM).filter(UserORM.email == user.email).first()
    if not db_user or not check_password_hash(db_user.password, user.password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = create_access_token({"sub": db_user.email, "role": db_user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": db_user.username
        }
    }

def get_current_user(authorization: str = Header(...)):
    token = authorization.split(" ")[1] if " " in authorization else authorization
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    return payload

@router.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {
        "message": f"Olá, {current_user['sub']}! Acesso permitido.",
        "role": current_user["role"]
    }


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    db = SessionLocal()
    try:
        user = db.query(UserORM).filter(UserORM.email == data.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Gera token válido por 15 minutos
        token = create_access_token({"sub": user.email}, expires_minutes=15)
        reset_link = f"http://localhost:4200/reset-password?token={token}"

        print(f"\n🔗 Link de redefinição de senha:\n{reset_link}\n")
        return {"message": "Se o e-mail estiver correto, um link foi enviado (simulado)."}
    finally:
        db.close()


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    db = SessionLocal()
    try:
        payload = verify_token(data.token)
        if not payload:
            raise HTTPException(status_code=401, detail="Token inválido ou expirado")

        email = payload.get("sub")
        user = db.query(UserORM).filter(UserORM.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        hashed_password = generate_password_hash(data.new_password)
        user.password = hashed_password
        db.commit()

        return {"message": "Senha redefinida com sucesso"}
    finally:
        db.close()