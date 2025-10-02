from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import BaseModel, EmailStr
from typing import List, Dict
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

# Caminho para a pasta de templates
template_folder = Path(__file__).parent.parent / 'templates'


conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("EMAIL_USER"),
    MAIL_PASSWORD=os.getenv("EMAIL_PASS"),
    MAIL_FROM=os.getenv("EMAIL_USER"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="GoGift", 
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=template_folder # Adiciona a pasta de templates à configuração
)

fm = FastMail(conf)

async def send_email_with_template(subject: str, recipients: List[EmailStr], template_name: str, template_body: Dict):
    """
    Envia um e-mail usando um template HTML.
    """
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        template_body=template_body,
        subtype=MessageType.html
    )

    await fm.send_message(message, template_name=template_name)