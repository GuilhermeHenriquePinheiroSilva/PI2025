from sqlalchemy import Column, Integer, String, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.database.db_config import Base
from app.enums.roles import Role  

class EnterpriseORM(Base):
    __tablename__ = "enterprise"

   
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(SqlEnum(Role), nullable=False)
    cnpj = Column(String(18), unique=True, index=True, nullable=False)

    giftcards = relationship(
        "RegisterGiftCardORM",
        back_populates="enterprise",  
        cascade="all, delete-orphan"
    )