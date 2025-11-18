from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.db_config import get_db
from app.models.categories_orm import CategoriesORM 
from app.models.categories_models import Category, CategoryCreate
from app.auth.auth_bearer import get_current_admin

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)

# --- Rota Pública para Listar Categorias ---
@router.get("/", response_model=List[Category])
async def get_all_categories(db: Session = Depends(get_db)):
    categories = db.query(CategoriesORM).all()
    return categories

# --- Rota de Admin para Criar Categoria ---
@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate, 
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin)
):
    new_category = CategoriesORM(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

# --- Rota de Admin para Atualizar Categoria ---
@router.put("/{category_id}", response_model=Category)
async def update_category(
    category_id: int, 
    category_update: CategoryCreate, 
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin)
):
    db_category = db.query(CategoriesORM).filter(CategoriesORM.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    
    db_category.name = category_update.name
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int, 
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin)
):
    db_category = db.query(CategoriesORM).filter(CategoriesORM.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
        
    db.delete(db_category)
    db.commit()
    return None