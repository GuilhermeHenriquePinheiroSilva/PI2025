# app/models/giftcard_orm.py

import uuid
# Adicionar Numeric para o campo valor
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, CHAR, TypeDecorator, Numeric 
from sqlalchemy.orm import relationship
from app.database.db_config import Base

class GUID(TypeDecorator):
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        try:
            return uuid.UUID(value)
        except (ValueError, TypeError):
            return value

class RegisterGiftCardORM(Base):
    __tablename__ = "register_giftcards"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    
    # --- CAMPO NOVO ADICIONADO ---
    # Numeric(precision, scale) - ex: 10 dígitos no total, 2 depois da vírgula
    valor = Column(Numeric(10, 2), nullable=False) 
    
    description = Column(String(255), nullable=True)
    quantityavailable = Column(Integer, nullable=False)
    generaterandomly = Column(Boolean, default=False)
    codes = Column(String(1000), nullable=True)
    imageUrl = Column(String(255), nullable=True)

    user = relationship("UserORM", back_populates="giftcards")