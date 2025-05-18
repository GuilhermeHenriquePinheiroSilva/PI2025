from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.models.register_giftcard_models import RegisterGiftCard
from app.models.register_giftcard_orm import RegisterGiftCardORM
from app.database.db_config import SessionLocal
from app.auth.jwt_handler import verify_token

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(authorization: str = Header(...)):
    token = authorization.split(" ")[1] if " " in authorization else authorization
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    return payload

@router.post("/register-giftcard")
async def register_giftcard(giftcard: RegisterGiftCard, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        new_giftcard = RegisterGiftCardORM(
            titulo=giftcard.titulo,
            descricao=giftcard.descricao,
            quantidade=giftcard.quantidade,
            geracao_aleatoria=giftcard.geracao_aleatoria,
            codigos=giftcard.codigos
        )
        db.add(new_giftcard)
        db.commit()
        db.refresh(new_giftcard)
        return {
            "message": "Gift card registrado com sucesso",
            "data": {
                "titulo": giftcard.titulo,
                "descricao": giftcard.descricao,
                "quantidade": giftcard.quantidade,
                "geracao_aleatoria": giftcard.geracao_aleatoria,
                "codigos": giftcard.codigos,
                "imagem_url": giftcard.imagem_url
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao registrar gift card: {str(e)}")