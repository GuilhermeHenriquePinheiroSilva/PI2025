from app.database.db_config import engine, Base
import app.models

def init_db():
    print("Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("Banco de dados inicializado com sucesso.")

if __name__ == "__main__":
    init_db()