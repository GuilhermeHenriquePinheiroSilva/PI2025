import mercadopago
import os
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from typing import List

from app.database.db_config import get_db
from app.models.giftcard_orm import RegisterGiftCardORM, SoldGiftCardORM
from app.models.user_orm import UserORM
from app.enums.sold_status import SoldStatus
from app.security import get_current_user

# --- Configuração de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# --- Modelos Pydantic para o Corpo da Requisição ---
class CartItem(BaseModel):
    product_id: uuid.UUID
    quantity: int

class CartCheckout(BaseModel):
    items: List[CartItem]


@router.post("/create_preference_cart", status_code=status.HTTP_201_CREATED)
async def create_preference_cart(
    cart: CartCheckout, # Recebe o carrinho no corpo da requisição
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    logging.info(f"Iniciando criação de preferência para um carrinho pelo user_id: {current_user.id}")

    preference_items = []
    external_reference_parts = []

    if not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O carrinho não pode estar vazio.")

    for item in cart.items:
        db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == item.product_id).first()

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

    # --- Dados da Preferência ---
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

# O Webhook continua o mesmo, mas a função de processamento será alterada
@router.post("/webhook")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
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

        if payment_info.get("status") != "approved":
            logging.info(f"Pagamento {payment_id} não está 'approved'. Status atual: '{payment_info.get('status')}'. Nenhuma ação tomada.")
            return Response(status_code=status.HTTP_200_OK)

        transaction_id = payment_info.get("id")
        existing_purchase = db.query(SoldGiftCardORM).filter(SoldGiftCardORM.transaction_id == str(transaction_id)).first()
        if existing_purchase:
            logging.warning(f"Pagamento {transaction_id} já foi processado anteriormente. Ignorando notificação duplicada.")
            return Response(status_code=status.HTTP_200_OK)

        logging.info(f"Pagamento {transaction_id} APROVADO. Iniciando processamento da compra com external_reference: {payment_info.get('external_reference')}")
        
        process_successful_payment(db, payment_info)

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


def process_successful_payment(db: Session, payment_info: dict):
    with db.begin_nested():
        external_ref = payment_info["external_reference"]
        transaction_id = str(payment_info["id"])
        
        try:
            # Novo formato: "user_id:id1,qt1;id2,qt2:uuid_unico"
            user_id_str, items_str, _ = external_ref.split(':')
            user_id = int(user_id_str)
            items_to_process = [item_str.split(',') for item_str in items_str.split(';')]
        except (ValueError, IndexError):
            logging.error(f"Formato de external_reference de carrinho inválido: '{external_ref}'")
            return

        db_user = db.query(UserORM).filter(UserORM.id == user_id).first()
        if not db_user:
            logging.error(f"Usuário {user_id} da external_reference não encontrado no DB.")
            # Se não encontrarmos o usuário, não há o que fazer. Reembolso seria complexo.
            return

        # Itera sobre cada item que foi pago
        for giftcard_id_str, quantity_str in items_to_process:
            giftcard_id = uuid.UUID(giftcard_id_str)
            quantity = int(quantity_str)
            
            logging.info(f"Processando item: Giftcard ID {giftcard_id}, Quantidade: {quantity}")

            db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).with_for_update().first()

            # Validações por item (essencial dentro do loop)
            if not db_giftcard or db_giftcard.quantityavailable < quantity:
                logging.critical(f"Estoque para o item {giftcard_id} tornou-se insuficiente APÓS o pagamento. Reembolsando a transação inteira...")
                sdk.refund().create(transaction_id)
                # Importante: para a execução e reverte a transação do banco de dados
                raise SQLAlchemyError(f"Estoque insuficiente para {giftcard_id} durante o processamento do webhook.")

            # Lógica para obter os códigos (igual à anterior)
            codes_to_sell = []
            if db_giftcard.generaterandomly:
                for _ in range(quantity):
                    codes_to_sell.append(str(uuid.uuid4()))
            else:
                all_codes = {code.strip() for code in (db_giftcard.codes or "").split(';') if code.strip()}
                sold_codes_query = db.query(SoldGiftCardORM.code).filter(SoldGiftCardORM.register_giftcard_id == giftcard_id).all()
                sold_codes = {code for (code,) in sold_codes_query}
                available_codes = list(all_codes - sold_codes)

                if len(available_codes) < quantity:
                    logging.critical(f"Estoque de CÓDIGOS para o item {giftcard_id} esgotou. Reembolsando...")
                    sdk.refund().create(transaction_id)
                    raise SQLAlchemyError(f"Estoque de códigos insuficiente para {giftcard_id} no webhook.")
                codes_to_sell = available_codes[:quantity]

            # Cria os registros de compra para este item
            for code in codes_to_sell:
                sold_card = SoldGiftCardORM(
                    code=code,
                    status=SoldStatus.VALID,
                    register_giftcard_id=db_giftcard.id,
                    owner_id=db_user.id,
                    transaction_id=transaction_id
                )
                db.add(sold_card)
            
            # Atualiza o estoque deste item
            db_giftcard.quantityavailable -= quantity
            logging.info(f"Item {db_giftcard.title} (x{quantity}) processado com sucesso.")

    db.commit()
    logging.info(f"SUCESSO TOTAL: Todos os {len(items_to_process)} tipos de itens do carrinho foram processados para o usuário {db_user.email}.")