from pydantic import BaseModel
from typing import Optional

class RegisterGiftCard(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    quantityavailable: int
    generaterandomly: bool = False
    codes: Optional[str] = None
    image: Optional[str] = None