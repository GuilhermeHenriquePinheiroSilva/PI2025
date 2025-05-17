from sqlalchemy import Column, Integer, String, Boolean
from app.database.db_config import Base

class RegisterGiftCardORM(Base):
    __tablename__ = "register_giftcards"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    quantityavailable = Column(Integer, nullable=False)
    generaterandomly = Column(Boolean, default=False)
    codes = Column(String(1000), nullable=True)
    image = Column(String(255), nullable=True)