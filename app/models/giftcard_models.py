from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import date

from app.enums.sold_status import SoldStatus 

# Este é o schema do produto base, que vamos aninhar
class RegisterGiftCardInfo(BaseModel):
    title: str
    valor: Decimal
    imageUrl: Optional[str] = None

    class Config:
        from_attributes = True

class RegisterGiftCard(BaseModel):
    id: Optional[UUID] = None
    user_id: int
    title: str
    valor: Decimal
    ativo: bool = True
    validade: Optional[date] = None
    nota: Optional[Decimal] = Field(default=None, ge=0, le=5)
    description: Optional[str] = None
    quantityavailable: int
    generaterandomly: bool = False
    codes: Optional[str] = None
    imageUrl: Optional[str] = None

    class Config:
        from_attributes = True

class SoldGiftCard(BaseModel):
    id: UUID
    code: str
    status: SoldStatus 
    purchase_date: date
    register_giftcard_id: UUID
    owner_id: int
    
    # NOVO: Adicione o relacionamento para carregar os detalhes do produto
    original_giftcard: RegisterGiftCardInfo

    class Config:
        from_attributes = True