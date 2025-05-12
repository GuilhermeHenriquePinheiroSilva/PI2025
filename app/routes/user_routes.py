from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from app.models.user_models import User, UserLogin
from app.models.user_orm import UserORM
from app.auth.jwt_handler import create_access_token, verify_token
from app.database.db_config import SessionLocal

router = APIRouter()

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

    hashed_password = bcrypt.hash(user.password)
    new_user = UserORM(
        username=user.username,
        email=user.email,
        password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Usuário registrado com sucesso", "user_id": new_user.id}

@router.post("/login")
async def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(UserORM).filter(UserORM.email == user.email).first()
    if not db_user or not bcrypt.verify(user.password, db_user.password):
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
