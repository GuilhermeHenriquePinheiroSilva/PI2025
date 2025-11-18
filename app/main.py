from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.order_cleanup_service import cancel_expired_pending_orders 

# Carrega as variáveis de ambiente do arquivo .env ANTES de qualquer outra importação de rotas
load_dotenv() 

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia o agendador quando a aplicação sobe
    scheduler.add_job(cancel_expired_pending_orders, 'interval', minutes=1, id="cancel_orders_job")
    scheduler.start()
    yield
    # Para o agendador quando a aplicação desce
    scheduler.shutdown()

# Importe todas as suas rotas
from app.routes import auth_routes, category_routes, order_routes,user_routes, giftcard_routes, enterprise_routes, mercadopago_routes, chatbot_routes, validation_routes

app = FastAPI(
    title="GoGift API",
    description="API para o sistema de gerenciamento de Gift Cards.",
    version="1.0.0",
    lifespan=lifespan
)

# --- CONFIGURAÇÃO DO CORS ---
# Permite a comunicação entre o seu front-end Angular e o back-end
origins = [
    "http://localhost:4200",
    "https://2ceeed3aa53d.ngrok-free.app", # <-- Adicione a URL https do seu ngrok aqui
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PASTA DE UPLOADS ---
# Define o diretório de forma relativa à raiz do projeto.
UPLOAD_DIRECTORY = "uploads"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# Serve os arquivos da pasta 'uploads' na URL '/uploads'
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIRECTORY), name="static_images")

# --- INCLUSÃO DAS ROTAS ---
app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(giftcard_routes.router) 
app.include_router(enterprise_routes.router)
app.include_router(mercadopago_routes.router)
app.include_router(chatbot_routes.router)
app.include_router(category_routes.router)
app.include_router(order_routes.router)
app.include_router(validation_routes.router)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bem-vindo à API GoGift!"}