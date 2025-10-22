import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
import mercadopago
import os
import uuid
from decimal import Decimal # <-- IMPORTAÇÃO ADICIONADA

from app.database.db_config import SessionLocal
from app.models.order_orm import OrderORM, OrderStatus, OrderItemORM, OrderItemStatus
from app.models.giftcard_orm import RegisterGiftCardORM
from app.services.email_service import send_email_with_template

# Configuração do Logging e do SDK do Mercado Pago
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
if not access_token:
    raise RuntimeError("MERCADOPAGO_ACCESS_TOKEN não configurada para o scheduler.")
sdk = mercadopago.SDK(access_token)


ORDER_EXPIRATION_MINUTES = 5

async def send_order_expired_email(order: OrderORM):
    """Prepara e envia o e-mail de pedido expirado."""
    email_body = {
        "username": order.owner_name,
        "order_id": str(order.id).split('-')[0]
    }
    await send_email_with_template(
        subject="Seu Pedido na GoGift Expirou",
        recipients=[order.owner.email],
        template_name="order_expired.html",
        template_body=email_body
    )

# <-- ASSINATURA DA FUNÇÃO ATUALIZADA
async def process_successful_order(db: Session, order: OrderORM, payment_info: dict):
    """Lógica para processar um pedido aprovado (reutilizada do webhook)."""
    logger.info(f"Scheduler: Processando pedido {order.id} como APROVADO.")
    
    # --- LÓGICA DE VALOR LÍQUIDO ADICIONADA ---
    net_received_amount = None
    if payment_info.get("transaction_details"):
        net_raw = payment_info.get("transaction_details", {}).get("net_received_amount")
        if net_raw is not None:
            try:
                net_received_amount = Decimal(str(net_raw))
            except Exception:
                 logging.warning(f"Scheduler: Não foi possível converter net_received_amount '{net_raw}' para Decimal.")
    
    order.net_amount = net_received_amount # <-- SALVANDO O VALOR LÍQUIDO
    # --- FIM DA LÓGICA ADICIONADA ---
    
    order.status = OrderStatus.APPROVED
    for item in order.items:
        giftcard = item.original_giftcard
        if giftcard.generaterandomly:
            item.final_giftcard_codes = str(uuid.uuid4())
        else:
            all_codes = {c.strip() for c in (giftcard.codes or "").split(';') if c.strip()}
            sold_codes_query = db.query(OrderItemORM.final_giftcard_codes).join(OrderORM).filter(
                OrderItemORM.register_giftcard_id == giftcard.id,
                OrderORM.status == OrderStatus.APPROVED
            ).all()
            sold_codes = {c.strip() for codes, in sold_codes_query if codes for c in codes.split(';')}
            available_codes = list(all_codes - sold_codes)
            if not available_codes:
                logger.error(f"Overbooking detectado pelo scheduler no pedido {order.id}!")
                # Idealmente, aqui deveria haver uma lógica de notificação para administradores
                continue
            item.final_giftcard_codes = available_codes[0]
    # Aqui você poderia reenviar o e-mail de confirmação se quisesse garantir
    # await send_purchase_confirmation_email(...)

async def cancel_expired_pending_orders():
    """
    Verifica pedidos pendentes, consulta o status no Mercado Pago e cancela se necessário.
    """
    db: Session = SessionLocal()
    try:
        logger.info("Scheduler: Iniciando verificação de pedidos pendentes expirados...")

        expiration_time = datetime.utcnow() - timedelta(minutes=ORDER_EXPIRATION_MINUTES)
        
        expired_orders = db.query(OrderORM).options(
            joinedload(OrderORM.items).joinedload(OrderItemORM.original_giftcard),
            joinedload(OrderORM.owner)
        ).filter(
            OrderORM.status == OrderStatus.PENDING,
            OrderORM.created_at < expiration_time
        ).all()

        if not expired_orders:
            logger.info("Scheduler: Nenhum pedido expirado encontrado.")
            return

        for order in expired_orders:
            payment_id = order.mercadopago_transaction_id
            final_status = None
            payment_info_response = None # <-- Adicionado para guardar a resposta

            # 1. CONSULTAR O MERCADO PAGO PRIMEIRO
            if payment_id and not payment_id.startswith("pref_"): 
                try:
                    payment_info_response = sdk.payment().get(payment_id) # <-- Guarda a resposta
                    if payment_info_response and payment_info_response["status"] == 200:
                        final_status = payment_info_response["response"].get("status")
                except Exception as e:
                    logger.error(f"Scheduler: Falha ao consultar o payment_id {payment_id} no Mercado Pago: {e}")

            # 2. DECIDIR A AÇÃO COM BASE NO STATUS
            if final_status == 'approved':
                # Caso raro: webhook falhou, mas o pagamento foi aprovado. Processamos a compra.
                
                # --- ALTERAÇÃO AQUI ---
                # Passa a resposta completa do pagamento para a função de processamento
                if payment_info_response and payment_info_response.get("response"):
                    payment_info = payment_info_response["response"]
                    await process_successful_order(db, order, payment_info)
                else:
                    logger.error(f"Scheduler: Status 'approved' para {order.id} mas payment_info estava indisponível.")
                # --- FIM DA ALTERAÇÃO ---
            else:
                # Se o status for 'rejected', 'cancelled' ou se a consulta falhou (None), cancelamos o pedido.
                logger.warning(f"Scheduler: Pedido {order.id} expirou (Status MP: {final_status}). Cancelando e retornando estoque.")
                
                for item in order.items:
                    if item.original_giftcard:
                        item.original_giftcard.quantityavailable += item.quantity
                
                order.status = OrderStatus.EXPIRED
                
                await send_order_expired_email(order)
        
        db.commit()
        logger.info(f"Scheduler: {len(expired_orders)} pedido(s) expirado(s) foram processados.")

    except Exception as e:
        logger.error(f"Scheduler: Erro CRÍTICO ao processar pedidos expirados: {e}")
        db.rollback()
    finally:
        db.close()