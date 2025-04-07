from fastapi import FastAPI, HTTPException, Depends, Header
from passlib.hash import bcrypt
from firebase_config import users_ref
from models import User, UserLogin
from auth import create_access_token, verify_token
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

@app.post("/register")
async def register_user(user: User):
    existing_users = users_ref.where("email", "==", user.email).get()
    if existing_users:
        raise HTTPException(status_code=400, detail="Email já registrado")

    hashed_password = bcrypt.hash(user.password)

    user_data = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "role": user.role
    }

    users_ref.add(user_data)
    return {"message": "Usuário registrado com sucesso"}

@app.post("/login")
async def login_user(user: UserLogin):
    user_docs = users_ref.where("email", "==", user.email).get()
    if not user_docs:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    user_data = user_docs[0].to_dict()
    if not bcrypt.verify(user.password, user_data["password"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = create_access_token({"sub": user_data["email"], "role": user_data["role"]})
    return {
    "access_token": token,
    "token_type": "bearer",
    "user": {
        "username": user_data["username"]
    }
}

def get_current_user(authorization: str = Header(...)):
    token = authorization.split(" ")[1] if " " in authorization else authorization
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    return payload

@app.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Olá, {current_user['sub']}! Acesso permitido.", "role": current_user["role"]}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)