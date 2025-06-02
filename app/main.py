from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import user_routes
from app.routes import giftcard_routes

app = FastAPI()

IMAGE_UPLOAD_DIRECTORY = r"C:\Users\0221432411009\Desktop\img-gc"


app.mount("/uploads", StaticFiles(directory=IMAGE_UPLOAD_DIRECTORY), name="static_images")

app.include_router(user_routes.router)
app.include_router(giftcard_routes.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"], # Garante que seu front Angular possa acessar a API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)