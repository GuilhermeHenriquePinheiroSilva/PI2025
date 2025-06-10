from sqlalchemy import Column, Integer, String, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.database.db_config import Base
from app.enums.roles import Role  # Supondo que seu Enum 'Role' está neste caminho

class EnterpriseORM(Base):
    __tablename__ = "empresas"

   
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(SqlEnum(Role), nullable=False)
    cnpj = Column(String(18), unique=True, index=True, nullable=False)

    giftcards = relationship(
        "RegisterGiftCardORM",
        back_populates="empresa",  # O back_populates será 'empresa'
        cascade="all, delete-orphan"
    )