from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.database.db_config import get_db
from app.auth.auth_bearer import get_current_admin
from app.security import get_current_user

from app.models.enterprise_orm import EmpresaORM, EnterpriseStatus
from app.models.enterprise_models import EnterpriseCreate, EnterpriseRejection, EnterpriseResponse
from app.models.user_orm import UserORM
from app.enums.roles import Role

from app.services.email_service import send_email_with_template


router = APIRouter(
    prefix="/enterprise",
    tags=["Enterprise"]
)

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