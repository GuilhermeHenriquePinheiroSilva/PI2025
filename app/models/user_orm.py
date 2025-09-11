from sqlalchemy import Column, Integer, String, Enum as SqlEnum, Boolean
from sqlalchemy.orm import relationship
from app.database.db_config import Base
from app.enums.roles import Role
from app.enums.tags import Tag

class UserORM(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    emailverified = Column(Boolean, default=False)  
    password = Column(String(255), nullable=False)
    role = Column(SqlEnum(Role), nullable=False)
    tags = Column(SqlEnum(Tag), nullable=True)

    
    # Gift cards que este usuário (empresa) cadastrou para vender
    giftcards = relationship(
        "RegisterGiftCardORM",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Gift cards que este usuário comprou
    purchased_giftcards = relationship(
        "SoldGiftCardORM",
        back_populates="owner",
        foreign_keys="[SoldGiftCardORM.owner_id]"
    )