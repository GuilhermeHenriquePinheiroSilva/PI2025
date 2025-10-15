from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from .order_orm import OrderStatus, OrderItemStatus # Importe o OrderItemStatus

# Define quais informações do Gift Card original devem ser incluídas
class GiftCardInfo(BaseModel):
    title: str
    imageUrl: Optional[str] = None
    valor: Decimal # Adicionado para consistência, caso precise no futuro

    class Config:
        from_attributes = True

class OrderItem(BaseModel):
    id: UUID
    register_giftcard_id: UUID
    quantity: int
    unit_price: Decimal
    final_giftcard_codes: Optional[str] = None
    used_codes: Optional[str] = None
    
    # --- CAMPO DE STATUS ADICIONADO AQUI ---
    status: OrderItemStatus

    original_giftcard: GiftCardInfo

    class Config:
        from_attributes = True

class Order(BaseModel):
    id: UUID
    owner_id: int
    owner_name: str
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime
    items: List[OrderItem] = []

    class Config:
        from_attributes = True