from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from decimal import Decimal

class RegisterGiftCard(BaseModel):
    id: Optional[UUID] = None
    user_id: Optional[int] = None
    empresa_id: Optional[int] = None
    title: str
    
    valor: Decimal

    description: Optional[str] = None
    quantityavailable: int
    generaterandomly: bool = False
    codes: Optional[str] = None
    imageUrl: Optional[str] = None

    class Config:
        from_attributes = True # Padrão Pydantic V2