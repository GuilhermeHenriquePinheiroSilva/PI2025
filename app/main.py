from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import user_routes
from app.routes import giftcard_routes
from pathlib import Path
import os

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_FILES_DIR = BASE_DIR / "static/uploads"
os.makedirs(STATIC_FILES_DIR, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=STATIC_FILES_DIR), name="static_uploads")

app.include_router(user_routes.router)
app.include_router(giftcard_routes.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"], # Garante que seu front Angular possa acessar a API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)