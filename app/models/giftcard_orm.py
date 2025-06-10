# app/models/giftcard_orm.py

import uuid
from decimal import Decimal
from sqlalchemy import (Integer, String, Boolean, Numeric, 
                        ForeignKey, CHAR, TypeDecorator)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db_config import Base

# A classe GUID para o tipo de ID personalizado continua a mesma
class GUID(TypeDecorator):
    impl = CHAR(36)
    cache_ok = True
    def process_bind_param(self, value, dialect):
        if value is None: return value
        return str(value)
    def process_result_value(self, value, dialect):
        if value is None: return value
        try: return uuid.UUID(value)
        except (ValueError, TypeError): return value

class RegisterGiftCardORM(Base):
    __tablename__ = "register_giftcards"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Sintaxe para chaves estrangeiras (ForeignKey) dentro de mapped_column
    # Usamos " | None " para indicar que a coluna pode ser nula (nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    enterprise_id: Mapped[int | None] = mapped_column(ForeignKey("enterprises.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quantityavailable: Mapped[int] = mapped_column(nullable=False)
    generaterandomly: Mapped[bool] = mapped_column(default=False)
    codes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    imageUrl: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Sintaxe para relacionamentos que apontam para as outras tabelas
    user: Mapped["UserORM"] = relationship(back_populates="giftcards")
    enterprise: Mapped["EnterpriseORM"] = relationship(back_populates="giftcards")