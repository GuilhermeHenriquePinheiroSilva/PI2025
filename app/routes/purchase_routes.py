from decimal import Decimal
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List
from pydantic import BaseModel, Field
from sqlalchemy import func, cast, Numeric

from app.database.db_config import get_db
from app.security import get_current_user
from app.models.user_orm import UserORM
from app.models.giftcard_orm import RegisterGiftCardORM, SoldGiftCardORM
from app.models.giftcard_models import SoldGiftCard
from app.enums.sold_status import SoldStatus
from app.enums.roles import Role

router = APIRouter(
    prefix="/actions",
    tags=["Actions"],
)

class RateGiftCardRequest(BaseModel):
    nota: int = Field(..., ge=1, le=5, description="A nota para o gift card, de 1 a 5.")

# ROTA DE COMPRA REATIVADA
@router.post("/purchase/{giftcard_id}", response_model=List[SoldGiftCard])
def purchase_giftcard(
    giftcard_id: uuid.UUID,
    quantity: int = Query(1, gt=0, description="A quantidade de gift cards que deseja comprar."),
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    
    # 1. Encontrar o "produto" gift card que está à venda
    db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).first()

    if not db_giftcard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift Card não encontrado.")
    if not db_giftcard.ativo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este Gift Card não está ativo para venda.")

    # 2. Lógica para obter os códigos disponíveis a partir do campo 'codes'
    if not db_giftcard.codes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este Gift Card não possui códigos disponíveis para venda.")

    # Pega todos os códigos únicos do campo, ignorando espaços e linhas vazias
    all_codes = {code.strip() for code in db_giftcard.codes.split(';') if code.strip()}

    # 3. Verificar quais códigos deste gift card já foram vendidos
    sold_codes_query = db.query(SoldGiftCardORM.code).filter(SoldGiftCardORM.register_giftcard_id == giftcard_id).all()
    sold_codes = {code for (code,) in sold_codes_query}

    # Calcula os códigos que ainda não foram vendidos
    available_codes = list(all_codes - sold_codes)

    # 4. Verificar se há estoque suficiente de códigos e de quantidade geral
    if len(available_codes) < quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Estoque de códigos insuficiente. Apenas {len(available_codes)} códigos únicos disponíveis.")
    if db_giftcard.quantityavailable < quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Estoque geral insuficiente. Apenas {db_giftcard.quantityavailable} unidades disponíveis.")

    # 5. Criar as instâncias dos gift cards vendidos para o usuário
    purchased_cards = []
    codes_to_sell = available_codes[:quantity] # Pega a quantidade exata de códigos necessários

    for code in codes_to_sell:
        sold_card = SoldGiftCardORM(
            code=code,
            status=SoldStatus.VALID,
            register_giftcard_id=db_giftcard.id,
            owner_id=current_user.id
        )
        db.add(sold_card)
        purchased_cards.append(sold_card)

    # 6. Atualizar o estoque geral e salvar tudo no banco
    db_giftcard.quantityavailable -= quantity
    db.commit()

    for card in purchased_cards:
        db.refresh(card) # Atualiza as instâncias com os dados do banco (como ID e datas)

    return purchased_cards


@router.get("/my-purchases", response_model=List[SoldGiftCard])
def get_my_purchases(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    return db.query(SoldGiftCardORM).options(
        joinedload(SoldGiftCardORM.original_giftcard)
    ).filter(SoldGiftCardORM.owner_id == current_user.id).all()


@router.post("/rate/{sold_giftcard_id}", status_code=status.HTTP_200_OK)
def rate_giftcard(
    sold_giftcard_id: uuid.UUID,
    rating: RateGiftCardRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    sold_giftcard = db.query(SoldGiftCardORM).filter(SoldGiftCardORM.id == sold_giftcard_id).first()

    if not sold_giftcard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compra de Gift Card não encontrada.")
    if sold_giftcard.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem permissão para avaliar este Gift Card.")
    if sold_giftcard.nota is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta compra já foi avaliada.")

    sold_giftcard.nota = rating.nota
    register_giftcard_id = sold_giftcard.register_giftcard_id
    
    # --- INÍCIO DA CORREÇÃO ---
    # Calcula a média, forçando o tipo da coluna 'nota' para Numeric
    avg_rating_query_result = db.query(
        func.avg(cast(SoldGiftCardORM.nota, Numeric))
    ).filter(
        SoldGiftCardORM.register_giftcard_id == register_giftcard_id,
        SoldGiftCardORM.nota.isnot(None)
    ).scalar()
    # --- FIM DA CORREÇÃO ---

    register_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == register_giftcard_id).first()
    
    if register_giftcard:
        if avg_rating_query_result is not None:
            rounded_avg = round(Decimal(avg_rating_query_result), 1)
            register_giftcard.nota = rounded_avg
        else:
            register_giftcard.nota = None

    db.commit()

    return {"message": "Avaliação enviada com sucesso!"}