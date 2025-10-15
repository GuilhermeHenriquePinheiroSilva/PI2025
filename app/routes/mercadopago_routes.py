import mercadopago
import os
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from typing import List
from decimal import Decimal
from datetime import datetime, timedelta, timezone

from app.database.db_config import get_db
from app.models.giftcard_orm import RegisterGiftCardORM
from app.models.user_orm import UserORM
from app.security import get_current_user
from app.services.email_service import send_email_with_template
from app.models.order_orm import OrderORM, OrderItemORM, OrderStatus

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter(
    prefix="/mercadopago",
    tags=["MercadoPago"],
)

access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
if not access_token:
    logging.error("Variável de ambiente MERCADOPAGO_ACCESS_TOKEN não foi definida!")
    raise RuntimeError("MERCADOPAGO_ACCESS_TOKEN não configurada.")
sdk = mercadopago.SDK(access_token)

class CartItem(BaseModel):
    product_id: uuid.UUID
    quantity: int

class CartCheckout(BaseModel):
    items: List[CartItem]


# --- FUNÇÕES AUXILIARES DE E-MAIL ---
def send_payment_pending_email(background_tasks: BackgroundTasks, order: OrderORM, items_details: List[dict]):
    email_body = {
        "username": order.owner_name,
        "order_id": str(order.id),
        "items": items_details,
        "total_price": float(order.total_amount)
    }
    background_tasks.add_task(
        send_email_with_template,
        subject="Seu Pedido na GoGift está Aguardando Pagamento",
        recipients=[order.owner.email],
        template_name="purchase_pending.html",
        template_body=email_body
    )

def send_purchase_confirmation_email(background_tasks: BackgroundTasks, order: OrderORM):
    base_url = os.getenv("FRONTEND_URL", "http://localhost:4200")
    items_details = [
        {
            "title": item.original_giftcard.title,
            "quantity": item.quantity,
            "subtotal": float(item.unit_price * item.quantity)
        } for item in order.items
    ]
    
    email_body = {
        "username": order.owner_name,
        "order_id": str(order.id),
        "items": items_details,
        "total_price": float(order.total_amount),
        "base_url": base_url
    }
    
    background_tasks.add_task(
        send_email_with_template,
        subject="Sua Compra na GoGift foi Confirmada!",
        recipients=[order.owner.email],
        template_name="purchase_confirmation.html",
        template_body=email_body
    )

def send_payment_rejected_email(background_tasks: BackgroundTasks, order: OrderORM, reason: str):
    email_body = {
        "username": order.owner_name,
        "order_id": str(order.id).split('-')[0], # ID do Pedido adicionado
        "transaction_id": order.mercadopago_transaction_id or "N/A",
        "rejection_reason": reason
    }
    background_tasks.add_task(
        send_email_with_template,
        subject="Seu Pagamento foi Recusado - GoGift",
        recipients=[order.owner.email],
        template_name="payment_rejected.html",
        template_body=email_body
    )


# --- ROTAS PRINCIPAIS ---

@router.post("/create_preference_cart", status_code=status.HTTP_201_CREATED)
async def create_preference_cart(
    cart: CartCheckout,
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    if not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O carrinho não pode estar vazio.")

    total_amount = Decimal("0.0")
    order_items_to_create = []
    items_for_email = []
    preference_items = [] # Movido para fora do loop

    try:
        # 1. Validar estoque, calcular total e preparar dados
        for item in cart.items:
            db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == item.product_id).with_for_update().first()
            if not db_giftcard or not db_giftcard.ativo:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gift Card com ID {item.product_id} não está disponível.")
            if db_giftcard.quantityavailable < item.quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Estoque insuficiente para '{db_giftcard.title}'.")

            item_total = db_giftcard.valor * item.quantity
            total_amount += item_total
            
            # Adiciona o item à lista de preferência do MP
            preference_items.append({"title": db_giftcard.title, "quantity": item.quantity, "unit_price": float(db_giftcard.valor), "currency_id": "BRL"})
            items_for_email.append({"title": db_giftcard.title, "quantity": item.quantity, "subtotal": float(item_total)})

            # --- LÓGICA ALTERADA AQUI ---
            # Adiciona os itens individualmente para salvar no banco
            for _ in range(item.quantity):
                order_items_to_create.append({
                    "giftcard": db_giftcard,
                    "quantity": 1, # Quantidade é sempre 1 por item
                    "unit_price": db_giftcard.valor
                })

        # 2. Criar o Pedido (Order) com status PENDENTE
        new_order = OrderORM(owner_id=current_user.id, owner_name=current_user.username, total_amount=total_amount, status=OrderStatus.PENDING)
        db.add(new_order)
        db.flush() 
        new_order.owner = current_user

        # 3. Criar os Itens do Pedido (OrderItems) individualmente e reservar o estoque
        total_quantity_reserved = 0
        if order_items_to_create:
            first_giftcard = order_items_to_create[0]["giftcard"]
            for item_data in order_items_to_create:
                db.add(OrderItemORM(order_id=new_order.id, register_giftcard_id=item_data["giftcard"].id, quantity=1, unit_price=item_data["unit_price"]))
                total_quantity_reserved += 1
            
            # Reserva o estoque de uma vez
            first_giftcard.quantityavailable -= total_quantity_reserved


        send_payment_pending_email(background_tasks, new_order, items_for_email)

        # 4. Preparar e criar a preferência do Mercado Pago
        base_url = os.getenv("FRONTEND_URL", "http://localhost:4200")
        expiration_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        expiration_time_iso = expiration_time.isoformat("T", "milliseconds").replace('+00:00', 'Z')

        preference_data = {
            "items": preference_items,
            "back_urls": {"success": f"{base_url}/minhas-compras", "failure": f"{base_url}/cart", "pending": f"{base_url}/minhas-compras"},
            "auto_return": "approved",
            "external_reference": str(new_order.id),
            "notification_url": f"{os.getenv('BACKEND_PUBLIC_URL')}/api/mercadopago/webhook",
            "expires": True,
            "date_of_expiration": expiration_time_iso,
        }

        preference_response = sdk.preference().create(preference_data)
        if not (preference_response and preference_response.get("status") in [200, 201]):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao criar preferência de pagamento.")

        new_order.mercadopago_transaction_id = preference_response["response"].get("id")
        db.commit()

        return {"preference_id": preference_response["response"]["id"], "init_point": preference_response["response"]["init_point"]}

    except Exception as e:
        db.rollback()
        logging.critical(f"Erro ao criar preferência: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao processar o pedido.")


@router.post("/webhook")
async def mercadopago_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    body = await request.json()
    if body.get("type") != "payment":
        return Response(status_code=status.HTTP_200_OK)

    payment_id = body.get("data", {}).get("id")
    if not payment_id:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    try:
        payment_info_response = sdk.payment().get(payment_id)
        if not payment_info_response or payment_info_response.get("status") not in [200, 201]:
            logging.error(f"Não foi possível obter informações do Payment ID {payment_id}.")
            return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payment_info = payment_info_response["response"]
        order_id_str = payment_info.get("external_reference")
        payment_status = payment_info.get("status")

        order = db.query(OrderORM).options(joinedload(OrderORM.items).joinedload(OrderItemORM.original_giftcard), joinedload(OrderORM.owner)).filter(OrderORM.id == order_id_str).first()
        if not order or order.status != OrderStatus.PENDING:
            logging.warning(f"Pedido {order_id_str} não encontrado ou já processado.")
            return Response(status_code=status.HTTP_200_OK)

        order.mercadopago_transaction_id = str(payment_info.get("id"))

        if payment_status == "approved":
            order.status = OrderStatus.APPROVED
            
            # --- LÓGICA DE ATRIBUIÇÃO DE CÓDIGOS SIMPLIFICADA ---
            for item in order.items:
                giftcard = item.original_giftcard
                
                if giftcard.generaterandomly:
                    while True:
                        new_code = str(uuid.uuid4())
                        exists = db.query(OrderItemORM.id).filter(OrderItemORM.final_giftcard_codes.like(f"%{new_code}%")).first()
                        if not exists:
                            item.final_giftcard_codes = new_code
                            break
                else:
                    all_codes = {code.strip() for code in (giftcard.codes or "").split(';') if code.strip()}
                    sold_codes_query = db.query(OrderItemORM.final_giftcard_codes).join(OrderORM).filter(
                        OrderItemORM.register_giftcard_id == giftcard.id,
                        OrderORM.status == OrderStatus.APPROVED
                    ).all()
                    sold_codes = {c.strip() for codes, in sold_codes_query if codes for c in codes.split(';')}
                    
                    available_codes = list(all_codes - sold_codes)
                    if not available_codes:
                        logging.error(f"Overbooking no pedido {order.id} para o item {giftcard.id}. ESTORNAR!")
                        sdk.refund().create(payment_id)
                        order.status = OrderStatus.REFUNDED
                        break # Para o loop se um item falhar
                    
                    item.final_giftcard_codes = available_codes[0]

            if order.status != OrderStatus.REFUNDED:
                send_purchase_confirmation_email(background_tasks, order)

        elif payment_status in ["rejected", "cancelled", "refunded"]:
            order.status = OrderStatus.REJECTED
            for item in order.items:
                item.original_giftcard.quantityavailable += item.quantity # Devolve 1 por item
            
            rejection_reason = payment_info.get("status_detail", "Motivo não especificado.")
            send_payment_rejected_email(background_tasks, order, rejection_reason)
        
        db.commit()

    except Exception as e:
        db.rollback()
        logging.critical(f"Erro CRÍTICO no webhook para payment_id {payment_id}: {e}", exc_info=True)
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(status_code=status.HTTP_200_OK)