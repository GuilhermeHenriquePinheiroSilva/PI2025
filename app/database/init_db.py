from app.database.db_config import engine
from app.models.user_orm import Base

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Banco de dados inicializado com sucesso.")

if __name__ == "__main__":
    init_db()
