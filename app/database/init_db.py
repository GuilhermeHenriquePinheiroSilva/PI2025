from app.database.db_config import engine, Base
from app.models import user_orm
from app.models import giftcard_orm
from app.models import enterprise_orm
from app.models import categories_orm
from app.models import order_orm

def init_db():
    print("Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("Banco de dados inicializado com sucesso.")

if __name__ == "__main__":
    init_db()