import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List, Optional
from decimal import Decimal
from datetime import date

from app.database.db_config import get_db
from app.enums.sold_status import SoldStatus
from app.models.giftcard_orm import RegisterGiftCardORM, SoldGiftCardORM
from app.models.giftcard_models import RegisterGiftCard, SoldGiftCardDetails
from app.models.user_orm import UserORM
from app.security import get_current_user, enterprise_required

router = APIRouter(
    prefix="/giftcards",
    tags=["GiftCards"],
    responses={404: {"description": "Not found"}},
)

UPLOAD_DIRECTORY = "uploads"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

@router.post("/", response_model=RegisterGiftCard, status_code=status.HTTP_201_CREATED)
async def create_giftcard(
    title: str = Form(...),
    valor: Decimal = Form(...),
    quantityavailable: int = Form(...),
    category_id: Optional[int] = Form(None),
    validade: Optional[date] = Form(None),
    ativo: bool = Form(True),
    nota: Optional[Decimal] = Form(None),
    description: Optional[str] = Form(None),
    generaterandomly: bool = Form(False),
    codes: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    image_url = None
    if image:
        file_extension = os.path.splitext(image.filename)[1]
        image_name = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIRECTORY, image_name)
        with open(file_path, "wb") as buffer:
            buffer.write(await image.read())
        image_url = image_name

    db_giftcard = RegisterGiftCardORM(
        user_id=current_user.id,
        title=title,
        valor=valor,
        validade=validade,
        ativo=ativo,
        nota=nota,
        description=description,
        quantityavailable=quantityavailable,
        generaterandomly=generaterandomly,
        codes=codes,
        imageUrl=image_url,
        category_id=category_id
    )
    db.add(db_giftcard)
    db.commit()
    db.refresh(db_giftcard)
    return db_giftcard

@router.put("/{giftcard_id}", response_model=RegisterGiftCard)
async def update_giftcard(
    giftcard_id: uuid.UUID,
    current_user: UserORM = Depends(get_current_user),
    title: str = Form(...),
    valor: Decimal = Form(...),
    quantityavailable: int = Form(...),
    category_id: Optional[int] = Form(None),
    validade: Optional[date] = Form(None),
    ativo: bool = Form(True),
    nota: Optional[Decimal] = Form(None),
    description: Optional[str] = Form(None),
    generaterandomly: bool = Form(False),
    codes: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).first()
    if db_giftcard is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift Card not found")
    if db_giftcard.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform this action")

    image_url = db_giftcard.imageUrl
    if image:
        if image_url and os.path.exists(os.path.join(UPLOAD_DIRECTORY, image_url)):
            os.remove(os.path.join(UPLOAD_DIRECTORY, image_url))
        
        file_extension = os.path.splitext(image.filename)[1]
        image_name = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIRECTORY, image_name)
        with open(file_path, "wb") as buffer:
            buffer.write(await image.read())
        image_url = image_name
    
    db_giftcard.title = title
    db_giftcard.valor = valor
    db_giftcard.validade = validade
    db_giftcard.ativo = ativo
    db_giftcard.nota = nota
    db_giftcard.description = description
    db_giftcard.quantityavailable = quantityavailable
    db_giftcard.generaterandomly = generaterandomly
    db_giftcard.codes = codes
    db_giftcard.imageUrl = image_url,
    category_id=category_id

    db.commit()
    db.refresh(db_giftcard)
    return db_giftcard

@router.get("/me", response_model=List[RegisterGiftCard])
def read_my_giftcards(current_user: UserORM = Depends(get_current_user), db: Session = Depends(get_db)):
     return db.query(RegisterGiftCardORM).options(joinedload(RegisterGiftCardORM.category)).filter(RegisterGiftCardORM.user_id == current_user.id).all()

@router.get("/search/", response_model=List[RegisterGiftCard])
def search_giftcards(q: Optional[str] = None, db: Session = Depends(get_db)):
    # Inicia a query filtrando apenas os cards ativos
    query = db.query(RegisterGiftCardORM).options(joinedload(RegisterGiftCardORM.category)).filter(RegisterGiftCardORM.ativo == True)
  
    # Se um termo de busca for fornecido, adiciona o filtro de título
    if q:
        search_term = f"%{q}%"
        query = query.filter(RegisterGiftCardORM.title.ilike(search_term))
    
    return query.all()

@router.get("/category/{category_id}", response_model=List[RegisterGiftCard])
def get_giftcards_by_category(category_id: int, db: Session = Depends(get_db)):
    """
    Retorna uma lista de gift cards de uma categoria específica.
    """
    giftcards = db.query(RegisterGiftCardORM).options(joinedload(RegisterGiftCardORM.category)).filter(RegisterGiftCardORM.category_id == category_id, RegisterGiftCardORM.ativo == True).all()
    return giftcards

@router.get("/top-rated/", response_model=List[RegisterGiftCard])
def get_top_rated_giftcards(db: Session = Depends(get_db)):
    top_rated = db.query(RegisterGiftCardORM)\
        .options(joinedload(RegisterGiftCardORM.category))\
        .filter(RegisterGiftCardORM.ativo == True)\
        .filter(RegisterGiftCardORM.nota.isnot(None))\
        .order_by(desc(RegisterGiftCardORM.nota))\
        .limit(6)\
        .all()
    return top_rated

@router.get("/", response_model=List[RegisterGiftCard])
def read_all_giftcards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retorna uma lista de todos os gift cards que estão ATIVOS (público).
    """
    giftcards = db.query(RegisterGiftCardORM).options(joinedload(RegisterGiftCardORM.category)).filter(RegisterGiftCardORM.ativo == True).offset(skip).limit(limit).all()

    return giftcards

@router.get("/{giftcard_id}", response_model=RegisterGiftCard)
def read_giftcard_by_id(giftcard_id: uuid.UUID, db: Session = Depends(get_db)):
    db_giftcard = db.query(RegisterGiftCardORM).options(joinedload(RegisterGiftCardORM.category)).filter(RegisterGiftCardORM.id == giftcard_id).first()
    if db_giftcard is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift Card not found")
    return db_giftcard

@router.delete("/{giftcard_id}", response_model=RegisterGiftCard)
def delete_giftcard(
    giftcard_id: uuid.UUID, 
    current_user: dict = Depends(enterprise_required),
    db: Session = Depends(get_db)
):
    db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).first()
    if db_giftcard is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift Card not found")
        
    if db_giftcard.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform this action")

    if db_giftcard.imageUrl and os.path.exists(os.path.join(UPLOAD_DIRECTORY, db_giftcard.imageUrl)):
        os.remove(os.path.join(UPLOAD_DIRECTORY, db_giftcard.imageUrl))

    db.delete(db_giftcard)
    db.commit()
    return db_giftcard

@router.get("/codes/{giftcard_id}", response_model=List[str])
def get_giftcard_codes(giftcard_id: uuid.UUID, db: Session = Depends(get_db)):
    db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).first()
    if db_giftcard is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift Card not found")
    if not db_giftcard.codes:
        return []
    
    return db_giftcard.codes.split(';')


@router.get("/validate/{code}", response_model=SoldGiftCardDetails)
def validate_giftcard_code(code: str, db: Session = Depends(get_db), current_user: UserORM = Depends(enterprise_required)):
    sold_giftcard = db.query(SoldGiftCardORM)\
        .options(joinedload(SoldGiftCardORM.owner), joinedload(SoldGiftCardORM.original_giftcard))\
        .filter(SoldGiftCardORM.code == code).first()

    if not sold_giftcard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift Card não encontrado.")

    if sold_giftcard.original_giftcard.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este Gift Card não pertence à sua empresa.")

    return SoldGiftCardDetails(
        id=sold_giftcard.id,
        code=sold_giftcard.code,
        status=sold_giftcard.status,
        purchase_date=sold_giftcard.purchase_date,
        register_giftcard_id=sold_giftcard.register_giftcard_id,
        owner_id=sold_giftcard.owner_id,
        owner_name=sold_giftcard.owner.username,
        original_giftcard=sold_giftcard.original_giftcard
    )

# ROTA ATUALIZADA
@router.put("/validate/{code}/use", response_model=SoldGiftCardDetails)
def mark_giftcard_as_used(code: str, db: Session = Depends(get_db), current_user: UserORM = Depends(enterprise_required)):
    sold_giftcard = db.query(SoldGiftCardORM)\
        .options(joinedload(SoldGiftCardORM.owner), joinedload(SoldGiftCardORM.original_giftcard))\
        .filter(SoldGiftCardORM.code == code).first()

    if not sold_giftcard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift Card não encontrado.")

    if sold_giftcard.original_giftcard.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este Gift Card não pertence à sua empresa.")
    
    if sold_giftcard.status == SoldStatus.USED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este Gift Card já foi utilizado.")

    sold_giftcard.status = SoldStatus.USED
    db.commit()
    db.refresh(sold_giftcard)

    return SoldGiftCardDetails(
        id=sold_giftcard.id,
        code=sold_giftcard.code,
        status=sold_giftcard.status,
        purchase_date=sold_giftcard.purchase_date,
        register_giftcard_id=sold_giftcard.register_giftcard_id,
        owner_id=sold_giftcard.owner_id,
        owner_name=sold_giftcard.owner.username,
        original_giftcard=sold_giftcard.original_giftcard
    )
    
# NOVA ROTA PARA HISTÓRICO
@router.get("/used/me", response_model=List[SoldGiftCardDetails])
def get_my_used_giftcards(db: Session = Depends(get_db), current_user: UserORM = Depends(enterprise_required)):
    used_giftcards = db.query(SoldGiftCardORM)\
        .join(RegisterGiftCardORM)\
        .options(joinedload(SoldGiftCardORM.owner), joinedload(SoldGiftCardORM.original_giftcard))\
        .filter(RegisterGiftCardORM.user_id == current_user.id)\
        .filter(SoldGiftCardORM.status == SoldStatus.USED)\
        .order_by(desc(SoldGiftCardORM.purchase_date))\
        .all()

    # Mapeia para o DTO, garantindo que owner_name seja incluído
    return [
        SoldGiftCardDetails(
            id=gc.id,
            code=gc.code,
            status=gc.status,
            purchase_date=gc.purchase_date,
            register_giftcard_id=gc.register_giftcard_id,
            owner_id=gc.owner_id,
            owner_name=gc.owner.username,
            original_giftcard=gc.original_giftcard
        ) for gc in used_giftcards
    ]