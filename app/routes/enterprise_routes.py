from decimal import Decimal
import traceback
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Query
from pydantic import BaseModel
from sqlalchemy import extract, func, case, select
from sqlalchemy.orm import Session, selectinload, joinedload
from typing import List, Optional
import uuid

from app.database.db_config import get_db
from app.auth.auth_bearer import get_current_admin
from app.models.giftcard_orm import RegisterGiftCardORM
from app.models.order_orm import OrderORM, OrderItemORM, OrderStatus, OrderItemStatus
from app.models.order_models import OrderItemSchema
from app.security import enterprise_required, get_current_user

from app.models.enterprise_orm import EmpresaORM, EnterpriseStatus
from app.models.enterprise_models import EnterpriseCreate, EnterpriseRejection, EnterpriseResponse
from app.models.user_orm import UserORM
from app.enums.roles import Role

from app.services.email_service import send_email_with_template

import logging
import traceback
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/enterprise",
    tags=["Enterprise"]
)

class EnterpriseDashboardStats(BaseModel):
    total_sales_count: int
    total_sales_value: Decimal
    total_products_count: int
    total_stock_count: int

@router.get("/pending", response_model=List[EnterpriseResponse])
async def get_pending_enterprises(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin)
):
    pending_enterprises = db.query(EmpresaORM).filter(EmpresaORM.status == EnterpriseStatus.PENDING).all()
    return pending_enterprises

@router.get("/approved", response_model=List[EnterpriseResponse])
async def get_approved_enterprises(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin)
):
    approved_enterprises = db.query(EmpresaORM).filter(EmpresaORM.status == EnterpriseStatus.APPROVED).all()
    return approved_enterprises

@router.get("/rejected", response_model=List[EnterpriseResponse])
async def get_rejected_enterprises(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin)
):
    rejected_enterprises = db.query(EmpresaORM).filter(EmpresaORM.status == EnterpriseStatus.REJECTED).all()
    return rejected_enterprises

@router.get("/dashboard-stats", response_model=EnterpriseDashboardStats)
async def get_enterprise_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(enterprise_required) # Garante que o usuário é uma empresa
):

    # Calcula e retorna as estatísticas do dashboard para a empresa logada.
    if not current_user.enterprise_details:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Detalhes da empresa não encontrados para este usuário."
        )

    enterprise_id = current_user.enterprise_details.id
    user_id = current_user.id

    try:
        # 1. Total de Vendas (contagem de itens de pedidos pertencentes à empresa)
        total_sales_count = db.query(
            func.coalesce(func.count(OrderItemORM.id), 0)
        ).filter(
            OrderItemORM.enterprise_id == enterprise_id
        ).scalar()

        # 2. Valor Total Recebido
        total_sales_value = db.query(
            func.coalesce(func.sum(OrderItemORM.seller_amount), Decimal('0.00'))
        ).join(OrderORM).filter( # Join para filtrar pelo status do pedido pai
            OrderItemORM.enterprise_id == enterprise_id,
            OrderORM.status == OrderStatus.APPROVED # Considera apenas vendas concluídas/aprovadas
        ).scalar()

        # 3. Total de Produtos Cadastrados 
        total_products_count = db.query(
            func.coalesce(func.count(RegisterGiftCardORM.id), 0)
        ).filter(
            RegisterGiftCardORM.user_id == user_id
        ).scalar()

        # 4. Total em Estoque
        total_stock_count = db.query(
            func.coalesce(func.sum(RegisterGiftCardORM.quantityavailable), 0)
        ).filter(
            RegisterGiftCardORM.user_id == user_id
        ).scalar()

        stats_data = {
            "total_sales_count": total_sales_count,
            "total_sales_value": total_sales_value,
            "total_products_count": total_products_count,
            "total_stock_count": total_stock_count
        }
        return stats_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao calcular estatísticas do dashboard."
        )

@router.get("/me", response_model=EnterpriseResponse)
async def get_my_enterprise_details(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    enterprise = db.query(EmpresaORM).filter(EmpresaORM.user_id == current_user.id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma empresa associada a este usuário.")
    return enterprise


@router.get("/{enterprise_id}", response_model=EnterpriseResponse)
async def get_enterprise_by_id(enterprise_id: int, db: Session = Depends(get_db)):
    enterprise = db.query(EmpresaORM).filter(EmpresaORM.id == enterprise_id).first()
    if not enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")
    return enterprise

@router.post("/register", response_model=EnterpriseResponse, status_code=status.HTTP_201_CREATED)
async def register_enterprise(
    enterprise: EnterpriseCreate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    if db.query(EmpresaORM).filter(EmpresaORM.cnpj == enterprise.cnpj).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CNPJ já registrado")
    if current_user.enterprise_details:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário já possui uma empresa cadastrada")

    new_enterprise = EmpresaORM(
        **enterprise.model_dump(),
        user_id=current_user.id
    )
    new_enterprise.user = current_user
    db.add(new_enterprise)
    db.commit()
    db.refresh(new_enterprise)
    return new_enterprise


@router.put("/{enterprise_id}/approve", response_model=EnterpriseResponse)
async def approve_enterprise(
    enterprise_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin)
):
    db_enterprise = db.query(EmpresaORM).filter(EmpresaORM.id == enterprise_id).first()
    if not db_enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")

    db_enterprise.status = EnterpriseStatus.APPROVED
    db_enterprise.rejection_reason = None
    user_to_update = db_enterprise.user
    if user_to_update:
        user_to_update.role = Role.ENTERPRISE
        db.add(user_to_update)
    db.commit()
    db.refresh(db_enterprise)

    background_tasks.add_task(
        send_email_with_template,
        subject="Seu cadastro foi APROVADO! - GoGift",
        recipients=[db_enterprise.user.email],
        template_name="enterprise_approved.html",
        template_body={"enterprise_name": db_enterprise.nome_fantasia}
    )
    return db_enterprise


@router.put("/{enterprise_id}/reject", response_model=EnterpriseResponse)
async def reject_enterprise(
    enterprise_id: int,
    rejection_data: EnterpriseRejection,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_current_admin)
):
    db_enterprise = db.query(EmpresaORM).filter(EmpresaORM.id == enterprise_id).first()
    if not db_enterprise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")

    db_enterprise.status = EnterpriseStatus.REJECTED
    db_enterprise.rejection_reason = rejection_data.rejection_reason
    db.commit()
    db.refresh(db_enterprise)

    email_body = {
        "enterprise_name": db_enterprise.nome_fantasia,
        "rejection_reason": rejection_data.rejection_reason
    }

    background_tasks.add_task(
        send_email_with_template,
        subject="Atualização sobre seu cadastro - GoGift",
        recipients=[db_enterprise.user.email],
        template_name="enterprise_rejected.html",
        template_body=email_body
    )
    return db_enterprise

@router.get("/enterprise/sales", response_model=List[OrderItemSchema])
async def get_enterprise_sales(
    product_id: Optional[uuid.UUID] = Query(None, description="Filtrar por ID do Gift Card (RegisterGiftCardORM)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filtrar por mês (1-12)"),
    year: Optional[int] = Query(None, description="Filtrar por ano"),
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(enterprise_required) 
):
    if not current_user.enterprise_details:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Detalhes da empresa não encontrados para este usuário.")
    enterprise_id = current_user.enterprise_details.id

    query = db.query(OrderItemORM).filter(OrderItemORM.enterprise_id == enterprise_id)

    query = query.options(
        # Carrega o pedido E o usuário dono do pedido
        selectinload(OrderItemORM.order).selectinload(OrderORM.owner),
        # Carrega os detalhes do gift card original
        selectinload(OrderItemORM.original_giftcard)
    )

    if product_id:
        query = query.filter(OrderItemORM.register_giftcard_id == product_id)
    if year:
        query = query.join(OrderORM).filter(extract('year', OrderORM.created_at) == year)
    if month:
         if not year: # Adiciona o join apenas se ainda não foi feito pelo filtro de ano
             query = query.join(OrderORM)
         query = query.filter(extract('month', OrderORM.created_at) == month)

    if not year and not month:
        query = query.join(OrderORM)
    query = query.order_by(OrderORM.created_at.desc())

    sales_items = query.all()

    return sales_items