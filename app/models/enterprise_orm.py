from sqlalchemy import Column, Integer, String, Enum as SqlEnum, DateTime, ForeignKey
from app.enums.roles import Role
from app.database.db_config import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class EmpresaORM(Base):
    __tablename__ = "enterprise"

    id = Column(Integer, primary_key=True, index=True)
    nome_fantasia = Column(String(100), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=False, index=True)
    nome_admin_empresa = Column(String(50), nullable=False)
    cpf_adm = Column(String(14), unique=True, nullable=False)
    telefone = Column(String(20), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    senha = Column(String(255), nullable=False)
    role = Column(SqlEnum(Role), nullable=False)
    creation_date = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, unique=True)
    
    # NOVO: Define a relação
    user = relationship("UserORM", back_populates="enterprise_details")