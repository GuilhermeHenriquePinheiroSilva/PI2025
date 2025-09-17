import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database.db_config import get_db
from app.security import get_current_user
from app.models.user_orm import UserORM
from app.models.giftcard_orm import RegisterGiftCardORM, SoldGiftCardORM
from app.models.giftcard_models import SoldGiftCard
from app.enums.sold_status import SoldStatus
from app.enums.roles import Role # Importe o Enum de Roles

router = APIRouter(
    prefix="/actions",
    tags=["Actions"],
)

# @router.post("/purchase/{giftcard_id}", response_model=List[SoldGiftCard])
# def purchase_giftcard(
#     giftcard_id: uuid.UUID,
#     quantity: int = Query(1, gt=0, description="A quantidade de gift cards que deseja comprar."),
#     db: Session = Depends(get_db),
#     current_user: UserORM = Depends(get_current_user)
# ):
#     """
#     Endpoint para um usuário comprar um ou mais gift cards.
#     Utiliza os códigos pré-definidos no campo 'codes' do gift card.
#     """
    
#     # 1. Encontrar o "produto" gift card que está à venda
#     db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).first()

#     if not db_giftcard:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift Card não encontrado.")
#     if not db_giftcard.ativo:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este Gift Card não está ativo para venda.")

#     # 2. Lógica para obter os códigos disponíveis a partir do campo 'codes'
#     if not db_giftcard.codes:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este Gift Card não possui códigos disponíveis para venda.")

#     # Pega todos os códigos únicos do campo, ignorando espaços e linhas vazias
#     all_codes = {code.strip() for code in db_giftcard.codes.split(';') if code.strip()}

#     # 3. Verificar quais códigos deste gift card já foram vendidos
#     sold_codes_query = db.query(SoldGiftCardORM.code).filter(SoldGiftCardORM.register_giftcard_id == giftcard_id).all()
#     sold_codes = {code for (code,) in sold_codes_query}

#     # Calcula os códigos que ainda não foram vendidos
#     available_codes = list(all_codes - sold_codes)

#     # 4. Verificar se há estoque suficiente de códigos e de quantidade geral
#     if len(available_codes) < quantity:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Estoque de códigos insuficiente. Apenas {len(available_codes)} códigos únicos disponíveis.")
#     if db_giftcard.quantityavailable < quantity:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Estoque geral insuficiente. Apenas {db_giftcard.quantityavailable} unidades disponíveis.")

#     # 5. Criar as instâncias dos gift cards vendidos para o usuário
#     purchased_cards = []
#     codes_to_sell = available_codes[:quantity] # Pega a quantidade exata de códigos necessários

#     for code in codes_to_sell:
#         sold_card = SoldGiftCardORM(
#             code=code,
#             status=SoldStatus.VALID,
#             register_giftcard_id=db_giftcard.id,
#             owner_id=current_user.id
#         )
#         db.add(sold_card)
#         purchased_cards.append(sold_card)

#     # 6. Atualizar o estoque geral e salvar tudo no banco
#     db_giftcard.quantityavailable -= quantity
#     db.commit()

#     for card in purchased_cards:
#         db.refresh(card) # Atualiza as instâncias com os dados do banco (como ID e datas)

#     return purchased_cards


@router.get("/my-purchases", response_model=List[SoldGiftCard]) # <--- Nenhuma mudança aqui, mas confirme que o schema está correto
def get_my_purchases(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    """Retorna todos os gift cards comprados pelo usuário autenticado."""
    # A consulta já funciona por causa dos relacionamentos do SQLAlchemy
    return db.query(SoldGiftCardORM).filter(SoldGiftCardORM.owner_id == current_user.id).all()


@router.post("/validate/{code}", summary="Valida um código de Gift Card")
def validate_giftcard_code(
    code: str,
    db: Session = Depends(get_db),
    # A validação de código deve ser restrita.
    # Apenas o dono da loja (ENTERPRISE) ou um ADMIN pode validar.
    current_user: UserORM = Depends(get_current_user)
):
    """
    Valida um código de gift card e o marca como UTILIZADO.
    Apenas usuários ADMIN ou o dono do Gift Card (ENTERPRISE) podem usar este endpoint.
    """
    db_sold_card = db.query(SoldGiftCardORM).join(RegisterGiftCardORM).filter(SoldGiftCardORM.code == code).first()

    if not db_sold_card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código do Gift Card é inválido.")

    # Verifica se o usuário logado é ADMIN ou o dono do gift card original
    if not (current_user.role == Role.ADMIN or db_sold_card.original_giftcard.user_id == current_user.id):
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem permissão para validar este código.")

    if db_sold_card.status == SoldStatus.USED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este código já foi utilizado.")
        
    if db_sold_card.status == SoldStatus.EXPIRED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este código está expirado.")

    # Marcar como utilizado e salvar
    db_sold_card.status = SoldStatus.USED
    db.commit()

    return {"message": "Gift Card validado com sucesso!", "giftcard_id": db_sold_card.id, "status": "USED"}