from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database.db_config import get_db
from app.security import get_current_user
from app.models.user_orm import UserORM
from app.models.order_orm import OrderORM, OrderItemORM # Importe OrderItemORM
from app.models.order_models import Order as OrderSchema

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

@router.get("/me", response_model=List[OrderSchema])
async def get_my_orders(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    """
    Retorna o histórico de pedidos do usuário logado.
    """
    orders = db.query(OrderORM).options(
        # --- ALTERAÇÃO AQUI ---
        # Carrega os itens e, DENTRO de cada item, carrega também os dados do gift card original
        joinedload(OrderORM.items).joinedload(OrderItemORM.original_giftcard)
    ).filter(
        OrderORM.owner_id == current_user.id
    ).order_by(
        OrderORM.created_at.desc()
    ).all()
    
    return orders