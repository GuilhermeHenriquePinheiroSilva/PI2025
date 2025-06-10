# app/routes/giftcard_routes.py

import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
# 1. Importar Decimal para o campo valor
from decimal import Decimal

from app.database.db_config import get_db
from app.models import RegisterGiftCard, RegisterGiftCardORM

router = APIRouter(
    prefix="/giftcards",
    tags=["GiftCards"],
    responses={404: {"description": "Not found"}},
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIRECTORY = BASE_DIR / "static/uploads"

os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

@router.post("/", response_model=RegisterGiftCard)
async def create_giftcard(
    user_id: int = Form(...),
    title: str = Form(...),
    # --- 2. CAMPO 'valor' ADICIONADO AO FORMULÁRIO ---
    valor: Decimal = Form(...),
    quantityavailable: int = Form(...),
    description: Optional[str] = Form(None),
    generaterandomly: bool = Form(False),
    codes: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    image_url = None
    if image:
        file_extension = os.path.splitext(image.filename)[1]
        image_name = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIRECTORY, image_name)

        with open(file_path, "wb") as buffer:
            buffer.write(await image.read())
        image_url = f"/static/uploads/{image_name}"

    db_giftcard = RegisterGiftCardORM(
        user_id=user_id,
        title=title,
        valor=valor,
        description=description,
        quantityavailable=quantityavailable,
        generaterandomly=generaterandomly,
        codes=codes,
        imageUrl=image_url
    )
    db.add(db_giftcard)
    db.commit()
    db.refresh(db_giftcard)
    return db_giftcard

@router.put("/{giftcard_id}", response_model=RegisterGiftCard)
async def update_giftcard(
    giftcard_id: uuid.UUID, 
    user_id: int = Form(...),
    title: str = Form(...),
    # --- 4. CAMPO 'valor' ADICIONADO AO FORMULÁRIO ---
    valor: Decimal = Form(...),
    quantityavailable: int = Form(...),
    description: Optional[str] = Form(None),
    generaterandomly: bool = Form(False),
    codes: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).first()
    if db_giftcard is None:
        raise HTTPException(status_code=404, detail="Gift Card not found")

    image_url = db_giftcard.imageUrl
    if image:
        if image_url and os.path.exists(os.path.join(UPLOAD_DIRECTORY, image_url)):
            os.remove(os.path.join(UPLOAD_DIRECTORY, image_url))
        
        file_extension = os.path.splitext(image.filename)[1]
        image_name = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIRECTORY, image_name)
        with open(file_path, "wb") as buffer:
            buffer.write(await image.read())
        image_url = image_name
        
    db_giftcard.user_id = user_id
    db_giftcard.title = title
    db_giftcard.valor = valor # <-- 5. Atualizando o valor no objeto ORM
    db_giftcard.description = description
    db_giftcard.quantityavailable = quantityavailable
    db_giftcard.generaterandomly = generaterandomly
    db_giftcard.codes = codes
    db_giftcard.imageUrl = image_url

    db.commit()
    db.refresh(db_giftcard)
    return db_giftcard

@router.get("/", response_model=List[RegisterGiftCard])
def read_giftcards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    giftcards = db.query(RegisterGiftCardORM).offset(skip).limit(limit).all()
    return giftcards

@router.get("/{giftcard_id}", response_model=RegisterGiftCard)
def read_giftcard(giftcard_id: uuid.UUID, db: Session = Depends(get_db)):
    db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).first()
    if db_giftcard is None:
        raise HTTPException(status_code=404, detail="Gift Card not found")
    return db_giftcard

@router.delete("/{giftcard_id}", response_model=RegisterGiftCard)
def delete_giftcard(giftcard_id: uuid.UUID, db: Session = Depends(get_db)):
    db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).first()
    if db_giftcard is None:
        raise HTTPException(status_code=404, detail="Gift Card not found")

    if db_giftcard.imageUrl and os.path.exists(os.path.join(UPLOAD_DIRECTORY, db_giftcard.imageUrl)):
        os.remove(os.path.join(UPLOAD_DIRECTORY, db_giftcard.imageUrl))

    db.delete(db_giftcard)
    db.commit()
    return db_giftcard

@router.get("/codes/{giftcard_id}", response_model=List[str])
def get_giftcard_codes(giftcard_id: uuid.UUID, db: Session = Depends(get_db)):
    db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).first()
    if db_giftcard is None:
        raise HTTPException(status_code=404, detail="Gift Card not found")
    if not db_giftcard.codes:
        return []
    
    return db_giftcard.codes.split(';')