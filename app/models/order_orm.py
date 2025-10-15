import uuid
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Numeric, DateTime, Enum as SqlEnum
)
from sqlalchemy.orm import relationship
from app.database.db_config import Base
from datetime import datetime
from app.models.giftcard_orm import GUID
from enum import Enum

# Enum para o status do Pedido
class OrderStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    REFUNDED = "REFUNDED"

# --- NOVO ENUM PARA O STATUS DO ITEM ---
class OrderItemStatus(str, Enum):
    VALID = "VALID"      # Códigos disponíveis para uso
    USED = "USED"        # Todos os códigos deste item foram usados
    PARTIALLY_USED = "PARTIALLY_USED" # Alguns códigos foram usados (para compras com qtd > 1)

class OrderORM(Base):
    __tablename__ = "orders"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner_name = Column(String(100), nullable=False)
    status = Column(SqlEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    total_amount = Column(Numeric(10, 2), nullable=False)
    mercadopago_transaction_id = Column(String(255), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("UserORM", back_populates="orders")
    items = relationship("OrderItemORM", back_populates="order", cascade="all, delete-orphan")

class OrderItemORM(Base):
    __tablename__ = "order_items"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    order_id = Column(GUID(), ForeignKey("orders.id"), nullable=False)
    register_giftcard_id = Column(GUID(), ForeignKey("register_giftcards.id"), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    # --- CAMPOS ATUALIZADOS E NOVOS ---
    final_giftcard_codes = Column(String(1000), nullable=True) # Códigos ainda não utilizados
    used_codes = Column(String(1000), nullable=True) # Códigos já utilizados
    status = Column(SqlEnum(OrderItemStatus), nullable=False, default=OrderItemStatus.VALID)
    
    order = relationship("OrderORM", back_populates="items")
    original_giftcard = relationship("RegisterGiftCardORM")