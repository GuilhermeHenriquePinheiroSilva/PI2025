# app/models/enterprise_orm.py

from sqlalchemy import Integer, String, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db_config import Base
from app.enums.roles import Role

class EnterpriseORM(Base):
    __tablename__ = "enterprises"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(SqlEnum(Role), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(18), unique=True, index=True, nullable=False)

    # A sintaxe para relacionamentos também usa Mapped
    giftcards: Mapped["list[RegisterGiftCardORM]"] = relationship(
        back_populates="enterprise",
        cascade="all, delete-orphan"
    )