# app/models/user_orm.py

from sqlalchemy import Integer, String, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db_config import Base
from app.enums.roles import Role

class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(SqlEnum(Role), nullable=False)

    # A sintaxe para relacionamentos também usa Mapped
    # O type hint em string "list[...]" previne erros de importação circular
    giftcards: Mapped[list["RegisterGiftCardORM"]] = relationship(
    "RegisterGiftCardORM", # <--- APENAS O NOME DA CLASSE
    back_populates="user",
    cascade="all, delete-orphan"
)