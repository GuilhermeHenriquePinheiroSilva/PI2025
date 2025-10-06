# import mercadopago
# import os
# import uuid
# import logging
# from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, BackgroundTasks
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import SQLAlchemyError
# from pydantic import BaseModel
# from typing import List

# from app.database.db_config import get_db
# from app.models.giftcard_orm import RegisterGiftCardORM, SoldGiftCardORM
# from app.models.user_orm import UserORM
# from app.enums.sold_status import SoldStatus
# from app.security import get_current_user
# from app.services.email_service import send_email_with_template

# # --- Configuração de Logging ---
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# router = APIRouter(
#     prefix="/mercadopago",
#     tags=["MercadoPago"],
# )

# # --- Inicialização do SDK ---
# access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
# if not access_token:
#     logging.error("Variável de ambiente MERCADOPAGO_ACCESS_TOKEN não foi definida!")
#     raise RuntimeError("MERCADOPAGO_ACCESS_TOKEN não configurada.")
# sdk = mercadopago.SDK(access_token)

# # --- Modelos Pydantic para o Corpo da Requisição ---
# class CartItem(BaseModel):
#     product_id: uuid.UUID
#     quantity: int

# class CartCheckout(BaseModel):
#     items: List[CartItem]


# @router.post("/create_preference_cart", status_code=status.HTTP_201_CREATED)
# async def create_preference_cart(
#     cart: CartCheckout,
#     db: Session = Depends(get_db),
#     current_user: UserORM = Depends(get_current_user)
# ):
#     logging.info(f"Iniciando criação de preferência para um carrinho pelo user_id: {current_user.id}")

#     preference_items = []
#     external_reference_parts = []

#     if not cart.items:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O carrinho não pode estar vazio.")

#     with db.begin_nested():
#         for item in cart.items:
#             db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == item.product_id).with_for_update().first()

#             if not db_giftcard:
#                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gift Card com ID {item.product_id} não encontrado.")
#             if not db_giftcard.ativo:
#                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"O Gift Card '{db_giftcard.title}' não está à venda.")
#             if db_giftcard.quantityavailable < item.quantity:
#                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Estoque insuficiente para '{db_giftcard.title}'.")

#             preference_items.append({
#                 "title": db_giftcard.title,
#                 "quantity": item.quantity,
#                 "unit_price": float(db_giftcard.valor),
#                 "currency_id": "BRL",
#             })
#             external_reference_parts.append(f"{item.product_id},{item.quantity}")

#     base_url = os.getenv("FRONTEND_URL", "http://localhost:4200")
#     items_ref_string = ";".join(external_reference_parts)
#     external_reference = f"{current_user.id}:{items_ref_string}:{uuid.uuid4()}"

#     preference_data = {
#         "items": preference_items,
#         "back_urls": {
#             "success": f"{base_url}/minhas-compras",
#             "failure": f"{base_url}/cart",
#             "pending": f"{base_url}/minhas-compras"
#         },
#         "auto_return": "approved",
#         "external_reference": external_reference,
#         "notification_url": f"{os.getenv('BACKEND_PUBLIC_URL')}/api/mercadopago/webhook"
#     }

#     try:
#         preference_response = sdk.preference().create(preference_data)
#         if preference_response and preference_response.get("status") in [200, 201]:
#             preference = preference_response["response"]
#             logging.info(f"Preferência de pagamento (carrinho) criada com sucesso. Preference ID: {preference['id']}")
#             return {"preference_id": preference["id"], "init_point": preference["init_point"]}
#         else:
#             logging.error(f"Erro na API do MP ao criar preferência de carrinho: {preference_response}")
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Resposta inválida da API do Mercado Pago.")
#     except Exception as e:
#         logging.critical(f"Exceção inesperada ao criar preferência de carrinho: {e}", exc_info=True)
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao se comunicar com o Mercado Pago.")

# @router.post("/webhook")
# async def mercadopago_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
#     logging.info("--- Notificação de Webhook do Mercado Pago recebida ---")
#     body = await request.json()

#     if body.get("type") != "payment":
#         logging.info(f"Tipo de notificação ignorado: {body.get('type')}")
#         return Response(status_code=status.HTTP_200_OK)

#     payment_id = body.get("data", {}).get("id")
#     if not payment_id:
#         logging.error(f"Webhook recebido sem 'data.id'. Body: {body}")
#         return Response(status_code=status.HTTP_400_BAD_REQUEST)

#     logging.info(f"Notificação recebida para o Payment ID: {payment_id}")

#     try:
#         payment_info_response = sdk.payment().get(payment_id)
#         if not payment_info_response or payment_info_response.get("status") not in [200, 201]:
#             logging.error(f"Não foi possível obter informações do Payment ID {payment_id}. Resposta: {payment_info_response}")
#             return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         payment_info = payment_info_response["response"]
#         payment_status = payment_info.get("status")
#         transaction_id = str(payment_info.get("id"))

#         is_already_processed = db.query(SoldGiftCardORM).filter(
#             SoldGiftCardORM.transaction_id == transaction_id,
#             SoldGiftCardORM.status == SoldStatus.VALID
#         ).first()

#         if is_already_processed:
#             logging.warning(f"Pagamento {transaction_id} já foi processado com SUCESSO. Ignorando notificação duplicada.")
#             return Response(status_code=status.HTTP_200_OK)
        
#         pending_cards = db.query(SoldGiftCardORM).filter(
#             SoldGiftCardORM.transaction_id == transaction_id,
#             SoldGiftCardORM.status == SoldStatus.PENDING
#         ).all()

#         if payment_status == "approved":
#             if pending_cards:
#                 logging.info(f"Atualizando compra PENDENTE {transaction_id} para APROVADA.")
#                 for card in pending_cards:
#                     card.status = SoldStatus.VALID
#                 db.commit()
#                 send_confirmation_email_for_purchase(background_tasks, pending_cards[0].owner, pending_cards)
#             else:
#                 logging.info(f"Pagamento {transaction_id} APROVADO diretamente. Processando nova compra.")
#                 process_new_successful_payment(db, payment_info, background_tasks)

#         elif payment_status in ["in_process", "pending"]:
#             if not pending_cards:
#                 logging.info(f"Pagamento {transaction_id} está PENDENTE. Reservando estoque.")
#                 process_pending_payment(db, payment_info, background_tasks)
#             else:
#                 logging.info(f"Pagamento {transaction_id} já registrado como PENDENTE. Nenhuma ação necessária.")

#         elif payment_status in ["rejected", "cancelled", "refunded"]:
#             if pending_cards:
#                 logging.warning(f"Pagamento {transaction_id} foi {payment_status.upper()}. Revertendo estoque.")
#                 revert_pending_purchase(db, pending_cards)
            
#             if payment_status == "rejected":
#                 send_rejection_email(db, background_tasks, payment_info)
        
#         else:
#             logging.info(f"Pagamento {transaction_id} com status '{payment_status}'. Nenhuma ação necessária no momento.")

#     except SQLAlchemyError as e:
#         db.rollback()
#         logging.critical(f"Erro de Banco de Dados ao processar webhook para payment_id {payment_id}: {e}", exc_info=True)
#         return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
#     except Exception as e:
#         db.rollback()
#         logging.critical(f"Erro CRÍTICO e inesperado ao processar webhook para payment_id {payment_id}: {e}", exc_info=True)
#         return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     logging.info(f"--- Fim do processamento do webhook para o Payment ID: {payment_id} ---")
#     return Response(status_code=status.HTTP_200_OK)

# # --- Funções Auxiliares Refatoradas ---

# def process_pending_payment(db: Session, payment_info: dict, background_tasks: BackgroundTasks):
#     with db.begin_nested():
#         external_ref = payment_info["external_reference"]
#         transaction_id = str(payment_info["id"])
        
#         try:
#             user_id_str, items_str, _ = external_ref.split(':')
#             user_id = int(user_id_str)
#             items_to_process = [item_str.split(',') for item_str in items_str.split(';')]
#         except (ValueError, IndexError):
#             logging.error(f"Formato de external_reference inválido ao processar pagamento pendente: '{external_ref}'")
#             raise SQLAlchemyError("Formato de external_reference inválido.")

#         db_user = db.query(UserORM).filter(UserORM.id == user_id).first()
#         if not db_user:
#             logging.error(f"Usuário {user_id} não encontrado para pagamento pendente.")
#             raise SQLAlchemyError("Usuário não encontrado.")

#         for giftcard_id_str, quantity_str in items_to_process:
#             giftcard_id = uuid.UUID(giftcard_id_str)
#             quantity = int(quantity_str)
            
#             db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).with_for_update().first()

#             if not db_giftcard or db_giftcard.quantityavailable < quantity:
#                 logging.warning(f"Estoque para o item {giftcard_id} insuficiente para reserva PENDENTE.")
#                 raise SQLAlchemyError(f"Estoque insuficiente para {giftcard_id} durante reserva.")

#             codes_to_sell = []
#             if db_giftcard.generaterandomly:
#                 for _ in range(quantity):
#                     while True:
#                         new_code = str(uuid.uuid4())
#                         exists = db.query(SoldGiftCardORM.id).filter(SoldGiftCardORM.code == new_code).first()
#                         if not exists:
#                             codes_to_sell.append(new_code)
#                             break
#             else:
#                 all_codes = {code.strip() for code in (db_giftcard.codes or "").split(';') if code.strip()}
#                 sold_codes_query = db.query(SoldGiftCardORM.code).filter(SoldGiftCardORM.register_giftcard_id == giftcard_id, SoldGiftCardORM.status.in_([SoldStatus.VALID, SoldStatus.PENDING])).all()
#                 sold_codes = {code for (code,) in sold_codes_query}
#                 available_codes = list(all_codes - sold_codes)

#                 if len(available_codes) < quantity:
#                     logging.warning(f"Estoque de CÓDIGOS para o item {giftcard_id} esgotou para a reserva PENDENTE.")
#                     raise SQLAlchemyError(f"Estoque de códigos insuficiente para {giftcard_id} na reserva.")
#                 codes_to_sell = available_codes[:quantity]

#             for code in codes_to_sell:
#                 sold_card = SoldGiftCardORM(code=code, status=SoldStatus.PENDING, register_giftcard_id=db_giftcard.id, owner_id=db_user.id, transaction_id=transaction_id)
#                 db.add(sold_card)
            
#             db_giftcard.quantityavailable -= quantity
#             logging.info(f"Item {db_giftcard.title} (x{quantity}) reservado com status PENDENTE.")
#     db.commit()

#     # --- NOVO: Envio do e-mail de pagamento pendente ---
#     pending_cards = db.query(SoldGiftCardORM).filter(SoldGiftCardORM.transaction_id == transaction_id).all()
#     send_pending_email_for_purchase(background_tasks, db_user, pending_cards)

# def process_new_successful_payment(db: Session, payment_info: dict, background_tasks: BackgroundTasks):
#     with db.begin_nested():
#         external_ref = payment_info["external_reference"]
#         transaction_id = str(payment_info["id"])
        
#         try:
#             user_id_str, items_str, _ = external_ref.split(':')
#             user_id = int(user_id_str)
#             items_to_process = [item_str.split(',') for item_str in items_str.split(';')]
#         except (ValueError, IndexError):
#             logging.error(f"Formato de external_reference inválido para aprovação direta: '{external_ref}'")
#             raise SQLAlchemyError("Formato de external_reference inválido.")

#         user = db.query(UserORM).filter(UserORM.id == user_id).first()
#         if not user:
#             logging.error(f"Usuário {user_id} não encontrado para aprovação direta.")
#             raise SQLAlchemyError("Usuário não encontrado.")

#         purchased_cards = []
#         for giftcard_id_str, quantity_str in items_to_process:
#             giftcard_id = uuid.UUID(giftcard_id_str)
#             quantity = int(quantity_str)

#             db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).with_for_update().first()

#             if not db_giftcard or db_giftcard.quantityavailable < quantity:
#                 logging.critical(f"Estoque para o item {giftcard_id} tornou-se insuficiente APÓS o pagamento. Reembolsando...")
#                 sdk.refund().create(transaction_id)
#                 error_reason = f"O estoque para o item '{db_giftcard.title if db_giftcard else 'desconhecido'}' se esgotou inesperadamente."
#                 email_body_error = {"username": user.username, "transaction_id": transaction_id, "error_reason": error_reason}
#                 background_tasks.add_task(send_email_with_template, subject="Problema no seu Pedido - GoGift", recipients=[user.email], template_name="purchase_error.html", template_body=email_body_error)
#                 raise SQLAlchemyError(f"Estoque insuficiente para {giftcard_id} durante o processamento do webhook.")

#             codes_to_sell = []
#             if db_giftcard.generaterandomly:
#                 for _ in range(quantity):
#                     while True:
#                         new_code = str(uuid.uuid4())
#                         exists = db.query(SoldGiftCardORM.id).filter(SoldGiftCardORM.code == new_code).first()
#                         if not exists:
#                             codes_to_sell.append(new_code)
#                             break
#             else:
#                 all_codes = {code.strip() for code in (db_giftcard.codes or "").split(';') if code.strip()}
#                 sold_codes_query = db.query(SoldGiftCardORM.code).filter(SoldGiftCardORM.register_giftcard_id == giftcard_id).all()
#                 sold_codes = {code for (code,) in sold_codes_query}
#                 available_codes = list(all_codes - sold_codes)

#                 if len(available_codes) < quantity:
#                     logging.critical(f"Estoque de CÓDIGOS para o item {giftcard_id} esgotou. Reembolsando...")
#                     sdk.refund().create(transaction_id)
#                     error_reason_codes = f"Não há códigos únicos suficientes para o item '{db_giftcard.title}'."
#                     email_body_error_codes = {"username": user.username, "transaction_id": transaction_id, "error_reason": error_reason_codes}
#                     background_tasks.add_task(send_email_with_template, subject="Problema no seu Pedido - GoGift", recipients=[user.email], template_name="purchase_error.html", template_body=email_body_error_codes)
#                     raise SQLAlchemyError(f"Estoque de códigos insuficiente para {giftcard_id} no webhook.")
#                 codes_to_sell = available_codes[:quantity]

#             for code in codes_to_sell:
#                 sold_card = SoldGiftCardORM(code=code, status=SoldStatus.VALID, register_giftcard_id=db_giftcard.id, owner_id=user.id, transaction_id=transaction_id)
#                 db.add(sold_card)
#                 purchased_cards.append(sold_card)
            
#             db_giftcard.quantityavailable -= quantity
#             logging.info(f"Item {db_giftcard.title} (x{quantity}) processado com sucesso.")

#     db.commit()
#     for card in purchased_cards:
#         db.refresh(card)
#     send_confirmation_email_for_purchase(background_tasks, user, purchased_cards)

# def revert_pending_purchase(db: Session, pending_cards: List[SoldGiftCardORM]):
#     with db.begin_nested():
#         for card in pending_cards:
#             card.original_giftcard.quantityavailable += 1
#             db.delete(card)
#     db.commit()

# def send_confirmation_email_for_purchase(background_tasks: BackgroundTasks, user: UserORM, sold_cards: List[SoldGiftCardORM]):
#     purchased_items_details = []
#     total_price = 0.0
#     for card in sold_cards:
#         unit_price = float(card.original_giftcard.valor)
#         total_price += unit_price
#         purchased_items_details.append({
#             "title": card.original_giftcard.title,
#             "quantity": 1, 
#             "unit_price": unit_price,
#             "subtotal": unit_price
#         })

#     email_body_success = {"username": user.username, "items": purchased_items_details, "total_price": total_price}
#     background_tasks.add_task(
#         send_email_with_template,
#         subject="Sua Compra na GoGift foi Confirmada!",
#         recipients=[user.email],
#         template_name="purchase_confirmation.html",
#         template_body=email_body_success
#     )
#     logging.info(f"SUCESSO TOTAL: Compra processada para o usuário {user.email}.")

# def send_rejection_email(db: Session, background_tasks: BackgroundTasks, payment_info: dict):
#     external_ref = payment_info.get("external_reference")
#     transaction_id = str(payment_info.get("id"))
#     try:
#         user_id_str, _, _ = external_ref.split(':')
#         user = db.query(UserORM).filter(UserORM.id == int(user_id_str)).first()
#         if user:
#             rejection_reason = payment_info.get("status_detail", "Motivo não especificado pelo processador de pagamento.")
#             email_body_rejected = {"username": user.username, "transaction_id": transaction_id, "rejection_reason": rejection_reason}
#             background_tasks.add_task(
#                 send_email_with_template,
#                 subject="Seu Pagamento foi Recusado - GoGift",
#                 recipients=[user.email],
#                 template_name="payment_rejected.html",
#                 template_body=email_body_rejected
#             )
#     except (ValueError, IndexError):
#         logging.error(f"Formato de external_reference inválido para pagamento recusado: '{external_ref}'")

# # --- NOVA FUNÇÃO AUXILIAR PARA O E-MAIL DE PENDÊNCIA ---
# def send_pending_email_for_purchase(background_tasks: BackgroundTasks, user: UserORM, sold_cards: List[SoldGiftCardORM]):
#     purchased_items_details = []
#     total_price = 0.0
#     for card in sold_cards:
#         unit_price = float(card.original_giftcard.valor)
#         total_price += unit_price
#         purchased_items_details.append({
#             "title": card.original_giftcard.title,
#             "quantity": 1, 
#             "unit_price": unit_price,
#             "subtotal": unit_price
#         })

#     email_body_pending = {"username": user.username, "items": purchased_items_details, "total_price": total_price}
#     background_tasks.add_task(
#         send_email_with_template,
#         subject="Seu Pedido na GoGift está Aguardando Pagamento",
#         recipients=[user.email],
#         template_name="purchase_pending.html",
#         template_body=email_body_pending
#     )
#     logging.info(f"E-mail de pagamento pendente enviado para o usuário {user.email}.")

import mercadopago
import os
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from typing import List

from app.database.db_config import get_db
from app.models.giftcard_orm import RegisterGiftCardORM, SoldGiftCardORM
from app.models.user_orm import UserORM
from app.enums.sold_status import SoldStatus
from app.security import get_current_user
from app.services.email_service import send_email_with_template

# --- Configuração de Logging e Constantes ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOW_STOCK_THRESHOLD = 5 

router = APIRouter(
    prefix="/mercadopago",
    tags=["MercadoPago"],
)

# --- Inicialização do SDK ---
access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
if not access_token:
    logging.error("Variável de ambiente MERCADOPAGO_ACCESS_TOKEN não foi definida!")
    raise RuntimeError("MERCADOPAGO_ACCESS_TOKEN não configurada.")
sdk = mercadopago.SDK(access_token)

# --- Modelos Pydantic ---
class CartItem(BaseModel):
    product_id: uuid.UUID
    quantity: int

class CartCheckout(BaseModel):
    items: List[CartItem]


@router.post("/create_preference_cart", status_code=status.HTTP_201_CREATED)
async def create_preference_cart(
    cart: CartCheckout,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    logging.info(f"Iniciando criação de preferência para um carrinho pelo user_id: {current_user.id}")

    preference_items = []
    external_reference_parts = []

    if not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O carrinho não pode estar vazio.")

    with db.begin_nested():
        for item in cart.items:
            db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == item.product_id).with_for_update().first()

            if not db_giftcard:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gift Card com ID {item.product_id} não encontrado.")
            if not db_giftcard.ativo:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"O Gift Card '{db_giftcard.title}' não está à venda.")
            if db_giftcard.quantityavailable < item.quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Estoque insuficiente para '{db_giftcard.title}'.")

            preference_items.append({
                "title": db_giftcard.title,
                "quantity": item.quantity,
                "unit_price": float(db_giftcard.valor),
                "currency_id": "BRL",
            })
            external_reference_parts.append(f"{item.product_id},{item.quantity}")

    base_url = os.getenv("FRONTEND_URL", "http://localhost:4200")
    items_ref_string = ";".join(external_reference_parts)
    external_reference = f"{current_user.id}:{items_ref_string}:{uuid.uuid4()}"

    preference_data = {
        "items": preference_items,
        "back_urls": {
            "success": f"{base_url}/minhas-compras",
            "failure": f"{base_url}/cart",
            "pending": f"{base_url}/minhas-compras"
        },
        "auto_return": "approved",
        "external_reference": external_reference,
        "notification_url": f"{os.getenv('BACKEND_PUBLIC_URL')}/api/mercadopago/webhook"
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        if preference_response and preference_response.get("status") in [200, 201]:
            preference = preference_response["response"]
            logging.info(f"Preferência de pagamento (carrinho) criada com sucesso. Preference ID: {preference['id']}")
            return {"preference_id": preference["id"], "init_point": preference["init_point"]}
        else:
            logging.error(f"Erro na API do MP ao criar preferência de carrinho: {preference_response}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Resposta inválida da API do Mercado Pago.")
    except Exception as e:
        logging.critical(f"Exceção inesperada ao criar preferência de carrinho: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao se comunicar com o Mercado Pago.")


@router.post("/webhook")
async def mercadopago_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    logging.info("--- Notificação de Webhook do Mercado Pago recebida ---")
    body = await request.json()

    if body.get("type") != "payment":
        logging.info(f"Tipo de notificação ignorado: {body.get('type')}")
        return Response(status_code=status.HTTP_200_OK)

    payment_id = body.get("data", {}).get("id")
    if not payment_id:
        logging.error(f"Webhook recebido sem 'data.id'. Body: {body}")
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    logging.info(f"Notificação recebida para o Payment ID: {payment_id}")

    try:
        payment_info_response = sdk.payment().get(payment_id)
        if not payment_info_response or payment_info_response.get("status") not in [200, 201]:
            logging.error(f"Não foi possível obter informações do Payment ID {payment_id}. Resposta: {payment_info_response}")
            return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payment_info = payment_info_response["response"]
        payment_status = payment_info.get("status")
        transaction_id = str(payment_info.get("id"))

        is_already_processed = db.query(SoldGiftCardORM).filter(
            SoldGiftCardORM.transaction_id == transaction_id,
            SoldGiftCardORM.status == SoldStatus.VALID
        ).first()

        if is_already_processed:
            logging.warning(f"Pagamento {transaction_id} já foi processado com SUCESSO. Ignorando notificação duplicada.")
            return Response(status_code=status.HTTP_200_OK)
        
        pending_cards = db.query(SoldGiftCardORM).filter(
            SoldGiftCardORM.transaction_id == transaction_id,
            SoldGiftCardORM.status == SoldStatus.PENDING
        ).all()

        if payment_status == "approved":
            if pending_cards:
                logging.info(f"Atualizando compra PENDENTE {transaction_id} para APROVADA.")
                with db.begin_nested():
                    for card in pending_cards:
                        card.status = SoldStatus.VALID
                        handle_enterprise_notifications(db, background_tasks, card.original_giftcard, quantity_sold=1)
                db.commit()
                send_confirmation_email_for_purchase(background_tasks, pending_cards[0].owner, pending_cards)
            else:
                logging.info(f"Pagamento {transaction_id} APROVADO diretamente. Processando nova compra.")
                process_new_successful_payment(db, payment_info, background_tasks)

        elif payment_status in ["in_process", "pending"]:
            if not pending_cards:
                logging.info(f"Pagamento {transaction_id} está PENDENTE. Reservando estoque.")
                process_pending_payment(db, payment_info, background_tasks)
            else:
                logging.info(f"Pagamento {transaction_id} já registrado como PENDENTE. Nenhuma ação necessária.")

        elif payment_status in ["rejected", "cancelled", "refunded"]:
            if pending_cards:
                logging.warning(f"Pagamento {transaction_id} foi {payment_status.upper()}. Revertendo estoque.")
                revert_pending_purchase(db, pending_cards)
            
            if payment_status == "rejected":
                send_rejection_email(db, background_tasks, payment_info)
        
        else:
            logging.info(f"Pagamento {transaction_id} com status '{payment_status}'. Nenhuma ação necessária no momento.")

    except SQLAlchemyError as e:
        db.rollback()
        logging.critical(f"Erro de Banco de Dados ao processar webhook para payment_id {payment_id}: {e}", exc_info=True)
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        db.rollback()
        logging.critical(f"Erro CRÍTICO e inesperado ao processar webhook para payment_id {payment_id}: {e}", exc_info=True)
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    logging.info(f"--- Fim do processamento do webhook para o Payment ID: {payment_id} ---")
    return Response(status_code=status.HTTP_200_OK)


# --- Funções Auxiliares Refatoradas ---

def process_pending_payment(db: Session, payment_info: dict, background_tasks: BackgroundTasks):
    with db.begin_nested():
        external_ref = payment_info["external_reference"]
        transaction_id = str(payment_info["id"])
        
        try:
            user_id_str, items_str, _ = external_ref.split(':')
            user_id = int(user_id_str)
            items_to_process = [item_str.split(',') for item_str in items_str.split(';')]
        except (ValueError, IndexError):
            logging.error(f"Formato de external_reference inválido ao processar pagamento pendente: '{external_ref}'")
            raise SQLAlchemyError("Formato de external_reference inválido.")

        db_user = db.query(UserORM).filter(UserORM.id == user_id).first()
        if not db_user:
            logging.error(f"Usuário {user_id} não encontrado para pagamento pendente.")
            raise SQLAlchemyError("Usuário não encontrado.")

        for giftcard_id_str, quantity_str in items_to_process:
            giftcard_id = uuid.UUID(giftcard_id_str)
            quantity = int(quantity_str)
            
            db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).with_for_update().first()

            if not db_giftcard or db_giftcard.quantityavailable < quantity:
                logging.warning(f"Estoque para o item {giftcard_id} insuficiente para reserva PENDENTE.")
                raise SQLAlchemyError(f"Estoque insuficiente para {giftcard_id} durante reserva.")

            if db_giftcard.quantityavailable > LOW_STOCK_THRESHOLD:
                db_giftcard.low_stock_notified = False

            codes_to_sell = []
            if db_giftcard.generaterandomly:
                for _ in range(quantity):
                    while True:
                        new_code = str(uuid.uuid4())
                        exists = db.query(SoldGiftCardORM.id).filter(SoldGiftCardORM.code == new_code).first()
                        if not exists:
                            codes_to_sell.append(new_code)
                            break
            else:
                all_codes = {code.strip() for code in (db_giftcard.codes or "").split(';') if code.strip()}
                sold_codes_query = db.query(SoldGiftCardORM.code).filter(SoldGiftCardORM.register_giftcard_id == giftcard_id, SoldGiftCardORM.status.in_([SoldStatus.VALID, SoldStatus.PENDING])).all()
                sold_codes = {code for (code,) in sold_codes_query}
                available_codes = list(all_codes - sold_codes)

                if len(available_codes) < quantity:
                    logging.warning(f"Estoque de CÓDIGOS para o item {giftcard_id} esgotou para a reserva PENDENTE.")
                    raise SQLAlchemyError(f"Estoque de códigos insuficiente para {giftcard_id} na reserva.")
                codes_to_sell = available_codes[:quantity]

            for code in codes_to_sell:
                sold_card = SoldGiftCardORM(code=code, status=SoldStatus.PENDING, register_giftcard_id=db_giftcard.id, owner_id=db_user.id, transaction_id=transaction_id)
                db.add(sold_card)
            
            db_giftcard.quantityavailable -= quantity
            logging.info(f"Item {db_giftcard.title} (x{quantity}) reservado com status PENDENTE.")
    db.commit()
    
    pending_cards = db.query(SoldGiftCardORM).filter(SoldGiftCardORM.transaction_id == transaction_id).all()
    send_pending_email_for_purchase(background_tasks, db_user, pending_cards)

def process_new_successful_payment(db: Session, payment_info: dict, background_tasks: BackgroundTasks):
    with db.begin_nested():
        external_ref = payment_info["external_reference"]
        transaction_id = str(payment_info["id"])
        
        try:
            user_id_str, items_str, _ = external_ref.split(':')
            user_id = int(user_id_str)
            items_to_process = [item_str.split(',') for item_str in items_str.split(';')]
        except (ValueError, IndexError):
            logging.error(f"Formato de external_reference inválido para aprovação direta: '{external_ref}'")
            raise SQLAlchemyError("Formato de external_reference inválido.")

        user = db.query(UserORM).filter(UserORM.id == user_id).first()
        if not user:
            logging.error(f"Usuário {user_id} não encontrado para aprovação direta.")
            raise SQLAlchemyError("Usuário não encontrado.")

        purchased_cards = []
        for giftcard_id_str, quantity_str in items_to_process:
            giftcard_id = uuid.UUID(giftcard_id_str)
            quantity = int(quantity_str)

            db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).with_for_update().first()

            if not db_giftcard or db_giftcard.quantityavailable < quantity:
                logging.critical(f"Estoque para o item {giftcard_id} tornou-se insuficiente APÓS o pagamento. Reembolsando...")
                sdk.refund().create(transaction_id)
                error_reason = f"O estoque para o item '{db_giftcard.title if db_giftcard else 'desconhecido'}' se esgotou inesperadamente."
                email_body_error = {"username": user.username, "transaction_id": transaction_id, "error_reason": error_reason}
                background_tasks.add_task(send_email_with_template, subject="Problema no seu Pedido - GoGift", recipients=[user.email], template_name="purchase_error.html", template_body=email_body_error)
                raise SQLAlchemyError(f"Estoque insuficiente para {giftcard_id} durante o processamento do webhook.")

            if db_giftcard.quantityavailable > LOW_STOCK_THRESHOLD:
                db_giftcard.low_stock_notified = False

            codes_to_sell = []
            if db_giftcard.generaterandomly:
                for _ in range(quantity):
                    while True:
                        new_code = str(uuid.uuid4())
                        exists = db.query(SoldGiftCardORM.id).filter(SoldGiftCardORM.code == new_code).first()
                        if not exists:
                            codes_to_sell.append(new_code)
                            break
            else:
                all_codes = {code.strip() for code in (db_giftcard.codes or "").split(';') if code.strip()}
                sold_codes_query = db.query(SoldGiftCardORM.code).filter(SoldGiftCardORM.register_giftcard_id == giftcard_id).all()
                sold_codes = {code for (code,) in sold_codes_query}
                available_codes = list(all_codes - sold_codes)

                if len(available_codes) < quantity:
                    logging.critical(f"Estoque de CÓDIGOS para o item {giftcard_id} esgotou. Reembolsando...")
                    sdk.refund().create(transaction_id)
                    error_reason_codes = f"Não há códigos únicos suficientes para o item '{db_giftcard.title}'."
                    email_body_error_codes = {"username": user.username, "transaction_id": transaction_id, "error_reason": error_reason_codes}
                    background_tasks.add_task(send_email_with_template, subject="Problema no seu Pedido - GoGift", recipients=[user.email], template_name="purchase_error.html", template_body=email_body_error_codes)
                    raise SQLAlchemyError(f"Estoque de códigos insuficiente para {giftcard_id} no webhook.")
                codes_to_sell = available_codes[:quantity]

            for code in codes_to_sell:
                sold_card = SoldGiftCardORM(code=code, status=SoldStatus.VALID, register_giftcard_id=db_giftcard.id, owner_id=user.id, transaction_id=transaction_id)
                db.add(sold_card)
                purchased_cards.append(sold_card)
            
            db_giftcard.quantityavailable -= quantity
            logging.info(f"Item {db_giftcard.title} (x{quantity}) processado com sucesso.")
            
            handle_enterprise_notifications(db, background_tasks, db_giftcard, quantity_sold=quantity)

    db.commit()
    for card in purchased_cards:
        db.refresh(card)
    send_confirmation_email_for_purchase(background_tasks, user, purchased_cards)

def revert_pending_purchase(db: Session, pending_cards: List[SoldGiftCardORM]):
    with db.begin_nested():
        for card in pending_cards:
            if card.original_giftcard.quantityavailable + 1 > LOW_STOCK_THRESHOLD:
                 card.original_giftcard.low_stock_notified = False
            card.original_giftcard.quantityavailable += 1
            db.delete(card)
    db.commit()

def send_confirmation_email_for_purchase(background_tasks: BackgroundTasks, user: UserORM, sold_cards: List[SoldGiftCardORM]):
    purchased_items_details = []
    total_price = 0.0
    for card in sold_cards:
        unit_price = float(card.original_giftcard.valor)
        total_price += unit_price
        purchased_items_details.append({
            "title": card.original_giftcard.title,
            "quantity": 1, 
            "unit_price": unit_price,
            "subtotal": unit_price
        })

    email_body_success = {"username": user.username, "items": purchased_items_details, "total_price": total_price}
    background_tasks.add_task(
        send_email_with_template,
        subject="Sua Compra na GoGift foi Confirmada!",
        recipients=[user.email],
        template_name="purchase_confirmation.html",
        template_body=email_body_success
    )
    logging.info(f"SUCESSO TOTAL: Compra processada para o usuário {user.email}.")

def send_rejection_email(db: Session, background_tasks: BackgroundTasks, payment_info: dict):
    external_ref = payment_info.get("external_reference")
    transaction_id = str(payment_info.get("id"))
    try:
        user_id_str, _, _ = external_ref.split(':')
        user = db.query(UserORM).filter(UserORM.id == int(user_id_str)).first()
        if user:
            rejection_reason = payment_info.get("status_detail", "Motivo não especificado pelo processador de pagamento.")
            email_body_rejected = {"username": user.username, "transaction_id": transaction_id, "rejection_reason": rejection_reason}
            background_tasks.add_task(
                send_email_with_template,
                subject="Seu Pagamento foi Recusado - GoGift",
                recipients=[user.email],
                template_name="payment_rejected.html",
                template_body=email_body_rejected
            )
    except (ValueError, IndexError):
        logging.error(f"Formato de external_reference inválido para pagamento recusado: '{external_ref}'")

def send_pending_email_for_purchase(background_tasks: BackgroundTasks, user: UserORM, sold_cards: List[SoldGiftCardORM]):
    purchased_items_details = []
    total_price = 0.0
    for card in sold_cards:
        unit_price = float(card.original_giftcard.valor)
        total_price += unit_price
        purchased_items_details.append({
            "title": card.original_giftcard.title,
            "quantity": 1, 
            "unit_price": unit_price,
            "subtotal": unit_price
        })

    email_body_pending = {"username": user.username, "items": purchased_items_details, "total_price": total_price}
    background_tasks.add_task(
        send_email_with_template,
        subject="Seu Pedido na GoGift está Aguardando Pagamento",
        recipients=[user.email],
        template_name="purchase_pending.html",
        template_body=email_body_pending
    )
    logging.info(f"E-mail de pagamento pendente enviado para o usuário {user.email}.")

def handle_enterprise_notifications(db: Session, background_tasks: BackgroundTasks, db_giftcard: RegisterGiftCardORM, quantity_sold: int):
    enterprise_user = db_giftcard.user
    if not enterprise_user:
        return

    # 1. Enviar e-mail de "Venda Realizada"
    sale_email_body = {
        "enterprise_name": enterprise_user.username,
        "product_title": db_giftcard.title,
        "quantity_sold": quantity_sold,
        "remaining_stock": db_giftcard.quantityavailable
    }
    background_tasks.add_task(
        send_email_with_template,
        subject=f"Nova Venda Realizada: {db_giftcard.title}",
        recipients=[enterprise_user.email],
        template_name="sale_notification.html",
        template_body=sale_email_body
    )
    logging.info(f"E-mail de venda realizada enviado para a empresa {enterprise_user.email}.")

    # 2. Verificar e enviar e-mail de "Estoque Baixo"
    if db_giftcard.quantityavailable <= LOW_STOCK_THRESHOLD and not db_giftcard.low_stock_notified:
        low_stock_email_body = {
            "enterprise_name": enterprise_user.username,
            "product_title": db_giftcard.title,
            "current_stock": db_giftcard.quantityavailable
        }
        background_tasks.add_task(
            send_email_with_template,
            subject=f"Alerta de Estoque Baixo: {db_giftcard.title}",
            recipients=[enterprise_user.email],
            template_name="low_stock_warning.html",
            template_body=low_stock_email_body
        )
        # Marca que a notificação foi enviada para não enviar novamente
        db_giftcard.low_stock_notified = True
        logging.info(f"E-mail de estoque baixo enviado para a empresa {enterprise_user.email}.")