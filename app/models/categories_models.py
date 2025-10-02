from pydantic import BaseModel, ConfigDict

# Modelo para o corpo da requisição de CRIAÇÃO ou ATUALIZAÇÃO
# Contém apenas os campos que o usuário deve enviar.
class CategoryCreate(BaseModel):
    name: str


class Category(CategoryCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)