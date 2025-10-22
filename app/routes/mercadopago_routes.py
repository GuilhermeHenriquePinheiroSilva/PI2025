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
from app.models.user_orm import UserORM # Importação para o joinedload
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
# (Já atualizadas para usar order.owner.username)
def send_payment_pending_email(background_tasks: BackgroundTasks, order: OrderORM, items_details: List[dict]):
    email_body = {
        "username": order.owner.username, # Busca o nome pelo relacionamento
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
        "username": order.owner.username, # Busca o nome pelo relacionamento
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
        "username": order.owner.username, # Busca o nome pelo relacionamento
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
    order_items_to_create = [] # Armazena dados para criar OrderItemORM
    items_for_email = []
    preference_items = []
    # enterprise_id = None # Removido - não valida mais empresa única

    try:
        # 1. Validar estoque, calcular total e preparar dados
        for item in cart.items:
            # Carrega giftcard, usuário dono e detalhes da empresa
            db_giftcard = db.query(RegisterGiftCardORM).options(
                joinedload(RegisterGiftCardORM.user).joinedload(UserORM.enterprise_details)
            ).filter(RegisterGiftCardORM.id == item.product_id).with_for_update().first()

            if not db_giftcard:
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gift Card com ID {item.product_id} não encontrado.")

            # Valida se o gift card pertence a uma empresa
            if not db_giftcard.user or not db_giftcard.user.enterprise_details:
                logging.error(f"Giftcard {db_giftcard.id} não possui uma empresa associada.")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este item não pode ser vendido.")

            # Validação de empresa única REMOVIDA

            if not db_giftcard.ativo:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gift Card com ID {item.product_id} não está disponível.")
            if db_giftcard.quantityavailable < item.quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Estoque insuficiente para '{db_giftcard.title}'.")

            item_selling_price = db_giftcard.valor # Usa o preço de venda já calculado
            item_total = item_selling_price * item.quantity
            total_amount += item_total

            preference_items.append({"title": db_giftcard.title, "quantity": item.quantity, "unit_price": float(item_selling_price), "currency_id": "BRL"})
            items_for_email.append({"title": db_giftcard.title, "quantity": item.quantity, "subtotal": float(item_total)})

            # Guarda os dados necessários para criar os OrderItemORM depois
            item_enterprise_id = db_giftcard.user.enterprise_details.id # ID da empresa deste item
            item_desired_amount = db_giftcard.desired_amount # Valor que a empresa quer receber
            for _ in range(item.quantity):
                order_items_to_create.append({
                    "giftcard_id": db_giftcard.id,
                    "enterprise_id": item_enterprise_id, # ID da empresa vendedora do item
                    "quantity": 1,
                    "unit_price": item_selling_price, # Preço de venda unitário
                    "seller_amount": item_desired_amount, # Valor a ser repassado à empresa
                    "giftcard_instance": db_giftcard # Referência para reserva de estoque
                })

        # 2. Criar o Pedido (Order) com status PENDENTE
        new_order = OrderORM(
            owner_id=current_user.id,
            # owner_name=current_user.username, # Removido
            total_amount=total_amount, # Total baseado nos preços de venda
            status=OrderStatus.PENDING
        )
        db.add(new_order)
        db.flush()
        new_order.owner = current_user # Associa para e-mails

        # 3. Criar os Itens do Pedido (OrderItems) e reservar estoque
        giftcards_stock_to_update = {} # {giftcard_id: quantity_to_reduce}
        if order_items_to_create:
            for item_data in order_items_to_create:
                db.add(OrderItemORM(
                    order_id=new_order.id,
                    register_giftcard_id=item_data["giftcard_id"],
                    enterprise_id=item_data["enterprise_id"], # Salva o ID da empresa no item
                    quantity=item_data["quantity"], # Sempre 1 neste loop
                    unit_price=item_data["unit_price"], # Preço de venda
                    seller_amount=item_data["seller_amount"] # Valor do vendedor
                ))
                # Agrupa a quantidade a ser reduzida por giftcard
                gc_id = item_data["giftcard_id"]
                giftcards_stock_to_update[gc_id] = giftcards_stock_to_update.get(gc_id, 0) + 1

            # Reserva o estoque para cada gift card afetado
            for gc_id, qty_reduce in giftcards_stock_to_update.items():
                 # Encontra a instância do giftcard (usando a referência salva)
                 giftcard_instance = next((item["giftcard_instance"] for item in order_items_to_create if item["giftcard_id"] == gc_id), None)
                 if giftcard_instance:
                     # Garante que não haja condição de corrida lendo o valor atual antes de subtrair
                     current_quantity = db.query(RegisterGiftCardORM.quantityavailable).filter(RegisterGiftCardORM.id == gc_id).scalar()
                     if current_quantity is not None and current_quantity >= qty_reduce:
                         giftcard_instance.quantityavailable = current_quantity - qty_reduce
                     else:
                         # Isso não deveria acontecer devido à validação anterior, mas é uma segurança extra
                         db.rollback()
                         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro de concorrência no estoque para '{giftcard_instance.title}'. Tente novamente.")
                 else:
                     # Fallback improvável: Rebusca e atualiza
                     db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == gc_id).update({"quantityavailable": RegisterGiftCardORM.quantityavailable - qty_reduce}, synchronize_session=False)


        send_payment_pending_email(background_tasks, new_order, items_for_email)

        # 4. Preparar e criar a preferência do Mercado Pago
        base_url = os.getenv("FRONTEND_URL", "http://localhost:4200")
        expiration_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        expiration_time_iso = expiration_time.isoformat("T", "milliseconds").replace('+00:00', 'Z')

        preference_data = {
            "items": preference_items, # Contém os preços de venda corretos
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

    except HTTPException as http_exc: # Captura HTTPExceptions primeiro para não logar como crítico
        db.rollback()
        raise http_exc # Re-levanta a exceção HTTP para o FastAPI tratar
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

        net_received_amount = None
        if payment_info.get("transaction_details"):
            net_raw = payment_info.get("transaction_details", {}).get("net_received_amount")
            if net_raw is not None:
                try:
                    # Converte o valor (que pode ser float ou int) para Decimal
                    net_received_amount = Decimal(str(net_raw))
                except Exception:
                    logging.warning(f"Não foi possível converter net_received_amount '{net_raw}' para Decimal.")

        # Carrega o Pedido, seus Itens, o Gift Card original E o Comprador (owner)
        order = db.query(OrderORM).options(
            joinedload(OrderORM.items).joinedload(OrderItemORM.original_giftcard),
            joinedload(OrderORM.owner) # Essencial para as funções de e-mail
        ).filter(OrderORM.id == order_id_str).first()

        if not order or order.status != OrderStatus.PENDING:
            logging.warning(f"Pedido {order_id_str} não encontrado ou já processado.")
            return Response(status_code=status.HTTP_200_OK)

        order.mercadopago_transaction_id = str(payment_info.get("id"))

        if payment_status == "approved":
            order.status = OrderStatus.APPROVED
            order.net_amount = net_received_amount # Salva o valor líquido

            # --- LÓGICA DE ATRIBUIÇÃO DE CÓDIGOS ---
            for item in order.items:
                giftcard = item.original_giftcard

                if giftcard.generaterandomly:
                    while True:
                        new_code = str(uuid.uuid4())
                        # Verifica se o código já existe em QUALQUER item de pedido
                        exists = db.query(OrderItemORM.id).filter(OrderItemORM.final_giftcard_codes.like(f"%{new_code}%")).first()
                        if not exists:
                            item.final_giftcard_codes = new_code
                            break
                else:
                    # Garante que estamos pegando a lista atual de códigos do BD
                    db.refresh(giftcard)
                    all_codes = {code.strip() for code in (giftcard.codes or "").split(';') if code.strip()}

                    # Busca códigos já vendidos E APROVADOS para ESTE TIPO de gift card
                    sold_codes_query = db.query(OrderItemORM.final_giftcard_codes).join(OrderORM).filter(
                        OrderItemORM.register_giftcard_id == giftcard.id,
                        OrderORM.status == OrderStatus.APPROVED,
                        OrderItemORM.final_giftcard_codes.isnot(None) # Ignora itens ainda não processados
                    ).all()
                    sold_codes = {c.strip() for codes, in sold_codes_query if codes for c in codes.split(';')}

                    available_codes = list(all_codes - sold_codes)
                    if not available_codes:
                        logging.error(f"Overbooking no pedido {order.id} para o item {giftcard.id}. ESTORNAR!")
                        # Tenta estornar o pagamento
                        try:
                            sdk.refund().create(payment_id)
                            order.status = OrderStatus.REFUNDED
                            # Idealmente, notificar admin e talvez enviar e-mail ao usuário de erro
                        except Exception as refund_error:
                            logging.critical(f"FALHA AO ESTORNAR pagamento {payment_id} por overbooking: {refund_error}")
                            # Marcar o pedido com um status especial ou logar para處理 manual
                        break # Para o loop de itens se um falhar e for estornado

                    # Atribui o primeiro código disponível
                    item.final_giftcard_codes = available_codes[0]

            # Envia e-mail de confirmação apenas se o pedido não foi estornado
            if order.status == OrderStatus.APPROVED:
                send_purchase_confirmation_email(background_tasks, order)

        elif payment_status in ["rejected", "cancelled", "refunded", "charged_back"]: # Adicionado chargeback
            # Se o pagamento falhou ou foi cancelado/estornado ANTES da nossa lógica,
            # precisamos devolver o estoque que foi reservado.
            original_status = order.status # Guarda o status caso precise saber se já foi processado
            order.status = OrderStatus.REJECTED if payment_status not in ["refunded", "charged_back"] else OrderStatus.REFUNDED
            order.net_amount = None

            # Devolve o estoque reservado na criação da preferência SOMENTE SE o pedido ainda estava PENDENTE
            if original_status == OrderStatus.PENDING:
                giftcards_stock_to_return = {} # {giftcard_id: quantity_to_return}
                for item in order.items:
                    gc_id = item.register_giftcard_id
                    giftcards_stock_to_return[gc_id] = giftcards_stock_to_return.get(gc_id, 0) + item.quantity

                for gc_id, qty_return in giftcards_stock_to_return.items():
                    # Usar synchronize_session='fetch' para garantir que a leitura ocorra antes da escrita na mesma transação
                    db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == gc_id).update(
                        {"quantityavailable": RegisterGiftCardORM.quantityavailable + qty_return},
                        synchronize_session='fetch'
                    )

            rejection_reason = payment_info.get("status_detail", "Motivo não especificado.")
            # Envia email de rejeição se o status final for REJECTED
            if order.status == OrderStatus.REJECTED:
                 send_payment_rejected_email(background_tasks, order, rejection_reason)
            # Poderia adicionar lógica para enviar e-mail específico de estorno/chargeback se necessário

        db.commit()

    except Exception as e:
        db.rollback()
        logging.critical(f"Erro CRÍTICO no webhook para payment_id {payment_id}: {e}", exc_info=True)
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(status_code=status.HTTP_200_OK)