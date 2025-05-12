from sqlalchemy import Column, Integer, String, Enum as SqlEnum
from app.database.db_config import Base
from app.enums.roles import Role

class UserORM(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(SqlEnum(Role), nullable=False)
