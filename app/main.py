# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv() 

# Importe suas rotas (agora sem user_routes)
from app.routes import auth_routes, giftcard_routes, purchase_routes, enterprise_routes, mercadopago_routes, chatbot_routes

app = FastAPI(
    title="GoGift API",
    description="API para o sistema de gerenciamento de Gift Cards.",
    version="1.0.0"
)

# --- CONFIGURAÇÃO DO CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PASTA DE UPLOADS ---
UPLOAD_DIRECTORY = "uploads"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIRECTORY), name="static_images")

# --- INCLUSÃO DAS ROTAS ---
app.include_router(auth_routes.router) # <-- Apenas este para autenticação
app.include_router(giftcard_routes.router)
app.include_router(purchase_routes.router) 
app.include_router(enterprise_routes.router)
app.include_router(mercadopago_routes.router)
app.include_router(chatbot_routes.router)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bem-vindo à API GoGift!"}