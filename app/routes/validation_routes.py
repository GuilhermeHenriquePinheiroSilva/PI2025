from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database.db_config import get_db
from app.models.order_orm import OrderItemORM, OrderItemStatus, OrderORM
from app.models.user_orm import UserORM
from app.models.giftcard_orm import RegisterGiftCardORM
from app.security import enterprise_required

router = APIRouter(
    prefix="/validation",
    tags=["Validation"]
)

# Rota para buscar um código e ver seus detalhes
@router.get("/{code}")
async def get_item_by_code(code: str, db: Session = Depends(get_db), current_user: UserORM = Depends(enterprise_required)):
    order_item = db.query(OrderItemORM).options(
        joinedload(OrderItemORM.order),
        joinedload(OrderItemORM.original_giftcard)
    ).filter(
        OrderItemORM.final_giftcard_codes.contains(code)
    ).first()

    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código não encontrado ou já utilizado.")

    if order_item.original_giftcard.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este Gift Card não pertence à sua empresa.")

    return order_item

# Rota para marcar um código como utilizado
@router.put("/{code}/use")
async def mark_code_as_used(code: str, db: Session = Depends(get_db), current_user: UserORM = Depends(enterprise_required)):
    order_item = db.query(OrderItemORM).options(
        joinedload(OrderItemORM.original_giftcard)
    ).filter(
        OrderItemORM.final_giftcard_codes.contains(code)
    ).first()

    if not order_item or order_item.original_giftcard.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código não encontrado ou inválido para esta empresa.")

    available_codes = [c.strip() for c in order_item.final_giftcard_codes.split(';') if c.strip()]
    used_codes = [c.strip() for c in (order_item.used_codes or "").split(';') if c.strip()]

    if code in available_codes:
        available_codes.remove(code)
        used_codes.append(code)

        order_item.final_giftcard_codes = ";".join(available_codes)
        order_item.used_codes = ";".join(used_codes)

        if not available_codes:
            order_item.status = OrderItemStatus.USED
        else:
            order_item.status = OrderItemStatus.PARTIALLY_USED
        
        db.commit()
        db.refresh(order_item)
        return order_item
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código já foi utilizado ou é inválido.")

# Rota para ver o histórico de códigos já utilizados pela empresa
@router.get("/history/me")
async def get_my_used_items(db: Session = Depends(get_db), current_user: UserORM = Depends(enterprise_required)):
    used_items = db.query(OrderItemORM).join(
        RegisterGiftCardORM, OrderItemORM.register_giftcard_id == RegisterGiftCardORM.id
    ).join( # --- ADICIONADO O JOIN FALTANTE ---
        OrderORM, OrderItemORM.order_id == OrderORM.id
    ).options(
        joinedload(OrderItemORM.order),
        joinedload(OrderItemORM.original_giftcard)
    ).filter(
        RegisterGiftCardORM.user_id == current_user.id,
        OrderItemORM.status.in_([OrderItemStatus.USED, OrderItemStatus.PARTIALLY_USED])
    ).order_by(
        OrderORM.created_at.desc() # Agora esta linha funcionará corretamente
    ).all()
    
    return used_items