from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
# Certifique-se de importar UserInfo ou defina OwnerInfo aqui
# from .user_models import UserInfo # Se UserInfo estiver em user_models.py
from .order_orm import OrderStatus, OrderItemStatus

# Define quais informações do Gift Card original devem ser incluídas
class GiftCardInfo(BaseModel):
    title: str
    imageUrl: Optional[str] = None
    valor: Decimal # Preço de venda

    class Config:
        from_attributes = True

# Define quais informações do Dono (Comprador) incluir
class OwnerInfo(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

# Define a estrutura do Pedido aninhado DENTRO do Item
class OrderInfoForOrderItem(BaseModel):
    owner_id: int
    created_at: datetime
    status: OrderStatus
    owner: Optional[OwnerInfo] = None # Inclui o objeto do dono aninhado

    class Config:
        from_attributes = True

# Schema principal para um Item de Pedido (usado na resposta da API)
class OrderItemSchema(BaseModel): # Renomeie se necessário
    id: UUID
    register_giftcard_id: UUID
    enterprise_id: int
    quantity: int
    unit_price: Decimal # Preço que o cliente pagou
    seller_amount: Decimal # Valor que a empresa recebe
    final_giftcard_codes: Optional[str] = None
    used_codes: Optional[str] = None
    status: OrderItemStatus # Status do código (VALID, USED, etc.)
    original_giftcard: GiftCardInfo # Informações do produto
    order: Optional[OrderInfoForOrderItem] = None # Informações do pedido pai (inclui data e comprador)

    class Config:
        from_attributes = True

# Schema principal para o Pedido (usado em /orders/me)
class OrderSchema(BaseModel): # Renomeie se necessário
    id: UUID
    owner_id: int
    status: OrderStatus # Status geral do pedido
    total_amount: Decimal # Valor total pago pelo cliente
    created_at: datetime
    items: List[OrderItemSchema] = [] # Lista de itens usando o schema acima
    owner: Optional[OwnerInfo] = None # Inclui informações do comprador no nível do pedido

    class Config:
        from_attributes = True