from sqlalchemy import Boolean, Column, Integer, String, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.database.db_config import Base
from app.enums.roles import Role
from app.enums.tags import Tag

class UserORM(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(SqlEnum(Role), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    
    giftcards = relationship(
        "RegisterGiftCardORM",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    purchased_giftcards = relationship(
        "SoldGiftCardORM",
        back_populates="owner",
        foreign_keys="[SoldGiftCardORM.owner_id]"
    )

    enterprise_details = relationship("EmpresaORM", back_populates="user", uselist=False)
    orders = relationship("OrderORM", back_populates="owner")