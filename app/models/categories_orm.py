from app.database.db_config import Base
from sqlalchemy import Column, Integer, String


class CategoriesORM(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)