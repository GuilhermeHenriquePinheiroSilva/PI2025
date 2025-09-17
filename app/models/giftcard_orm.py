import uuid
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey,
    CHAR, TypeDecorator, Numeric, Date, Enum as SqlEnum
)
from sqlalchemy.orm import relationship
from app.database.db_config import Base
from datetime import datetime

# Importa o Enum
from app.enums.sold_status import SoldStatus

class GUID(TypeDecorator):
    impl = CHAR(36)
    cache_ok = True
    def process_bind_param(self, value, dialect):
        if value is None: return value
        return str(value)
    def process_result_value(self, value, dialect):
        if value is None: return value
        try:
            return uuid.UUID(value)
        except (ValueError, TypeError):
            return value

class RegisterGiftCardORM(Base):
    __tablename__ = "register_giftcards"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    validade = Column(Date, nullable=True)
    nota = Column(Numeric(2, 1), nullable=True)
    description = Column(String(255), nullable=True)
    quantityavailable = Column(Integer, nullable=False)
    generaterandomly = Column(Boolean, default=False)
    codes = Column(String(1000), nullable=True) # Campo com os códigos separados por ;
    imageUrl = Column(String(255), nullable=True)

    user = relationship("UserORM", back_populates="giftcards")
    # Relacionamento para ver todos os cartões vendidos deste tipo
    sold_cards = relationship("SoldGiftCardORM", back_populates="original_giftcard", cascade="all, delete-orphan")


class SoldGiftCardORM(Base):
    __tablename__ = "sold_giftcards"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(SqlEnum(SoldStatus), nullable=False, default=SoldStatus.VALID)
    purchase_date = Column(Date, nullable=False, default=datetime.utcnow().date)

    # Chave estrangeira para o "produto" gift card que foi comprado
    register_giftcard_id = Column(GUID(), ForeignKey("register_giftcards.id"), nullable=False)
    # Chave estrangeira para o usuário que comprou o gift card
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    transaction_id = Column(String(255), index=True, nullable=True)

    # Relacionamentos
    original_giftcard = relationship("RegisterGiftCardORM", back_populates="sold_cards")
    owner = relationship("UserORM", back_populates="purchased_giftcards")