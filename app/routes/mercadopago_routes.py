import mercadopago
import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database.db_config import get_db
from app.models.giftcard_orm import RegisterGiftCardORM, SoldGiftCardORM
from app.models.user_orm import UserORM
from app.enums.sold_status import SoldStatus 
import uuid

router = APIRouter(
    prefix="/mercadopago",
    tags=["MercadoPago"],
)

# Inicializa o SDK do Mercado Pago com sua credencial
sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_ACCESS_TOKEN"))

@router.post("/create_preference/{giftcard_id}")
async def create_preference(
    giftcard_id: uuid.UUID,
    request: Request,
    quantity: int = 1,
    db: Session = Depends(get_db)
):
    """
    Cria uma preferência de pagamento no Mercado Pago para um Gift Card.
    """
    db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).first()

    if not db_giftcard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift Card não encontrado.")
    if not db_giftcard.ativo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este Gift Card não está à venda.")
    if db_giftcard.quantityavailable < quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estoque insuficiente.")

    # Dados da preferência de pagamento
    preference_data = {
        "items": [
            {
                "title": db_giftcard.title,
                "quantity": quantity,
                "unit_price": float(db_giftcard.valor),
                "currency_id": "BRL",
            }
        ],
        # --- ALTERAÇÃO IMPORTANTE ---
        # Usaremos URLs públicas como placeholder para o teste,
        # pois o Mercado Pago pode rejeitar 'localhost' ou '127.0.0.1'.
        "back_urls": {
            "success": "https://www.google.com/search?q=payment-success",
            "failure": "https://www.google.com/search?q=payment-failure",
            "pending": "https://www.google.com/search?q=payment-pending"
        },
        "auto_return": "approved",
        "external_reference": str(db_giftcard.id),
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        return {"preference_id": preference["id"], "init_point": preference["init_point"]}
    except Exception as e:
        # --- MELHORIA NO LOG DE ERRO ---
        # Esta linha irá imprimir o erro exato do Mercado Pago no seu terminal do backend.
        print(f"### ERRO AO CRIAR PREFERÊNCIA NO MERCADO PAGO: {e} ###")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
# ... (o resto do arquivo, incluindo a rota /webhook, continua o mesmo)
@router.post("/webhook")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook para receber notificações de pagamento do Mercado Pago.
    """
    body = await request.json()
    
    if body.get("type") == "payment":
        payment_id = body["data"]["id"]
        
        try:
            payment_info_response = sdk.payment().get(payment_id)
            payment_info = payment_info_response["response"]

            if payment_info["status"] == "approved":
                giftcard_id = uuid.UUID(payment_info["external_reference"])
                quantity = int(payment_info["additional_info"]["items"][0]["quantity"])
                payer_email = payment_info["payer"]["email"]
                
                db_user = db.query(UserORM).filter(UserORM.email == payer_email).first()
                if not db_user:
                    print(f"Webhook Warning: Usuário com email {payer_email} não encontrado no banco de dados.")
                    return {"status": "ok", "message": "User not found"}

                with db.begin_nested():
                    db_giftcard = db.query(RegisterGiftCardORM).filter(RegisterGiftCardORM.id == giftcard_id).with_for_update().first()

                    if not db_giftcard:
                        print(f"Webhook Error: Gift Card com ID {giftcard_id} não encontrado.")
                        return {"status": "error", "detail": "Giftcard not found"}

                    all_codes = {code.strip() for code in db_giftcard.codes.split(';') if code.strip()}
                    sold_codes_query = db.query(SoldGiftCardORM.code).filter(SoldGiftCardORM.register_giftcard_id == giftcard_id).all()
                    sold_codes = {code for (code,) in sold_codes_query}
                    available_codes = list(all_codes - sold_codes)

                    if len(available_codes) < quantity or db_giftcard.quantityavailable < quantity:
                        print(f"Webhook Error: Estoque insuficiente para o Gift Card {giftcard_id}.")
                        sdk.refund().create(payment_id)
                        raise HTTPException(status_code=500, detail="Estoque esgotado após pagamento. Reembolso iniciado.")

                    codes_to_sell = available_codes[:quantity]
                    for code in codes_to_sell:
                        sold_card = SoldGiftCardORM(
                            code=code,
                            status=SoldStatus.VALID,
                            register_giftcard_id=db_giftcard.id,
                            owner_id=db_user.id
                        )
                        db.add(sold_card)
                    
                    db_giftcard.quantityavailable -= quantity
                
                db.commit()
                print(f"Compra do Gift Card {giftcard_id} processada com sucesso para o usuário {db_user.email}.")

        except Exception as e:
            db.rollback()
            print(f"Erro ao processar webhook do Mercado Pago: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro no processamento do webhook")

    return {"status": "notification received"}
