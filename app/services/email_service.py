# app/services/email_service.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
# Carrega as variáveis de ambiente
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def send_verification_email(to_email: str, token: str):
    """
    Envia um email de verificação com link contendo o token JWT.
    """
    # Verificação inicial das credenciais
    if not EMAIL_USER or not EMAIL_PASS:
        print("\n!!! ERRO DE CONFIGURAÇÃO: As variáveis de ambiente EMAIL_USER e EMAIL_PASS não foram encontradas no .env.\n")
        return

    verification_link = f"http://localhost:8000/auth/verify-email?token={token}"
    subject = "Verifique seu endereço de email"
    body = f"""
    Olá,
    
    Clique no link abaixo para verificar seu email:
    {verification_link}
    
    Este link expira em 1 hora.
    """
    
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        print(f"\n--- Tentando enviar email de {EMAIL_USER} para {to_email} ---")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
        print("--- Email enviado com sucesso! ---\n")
    except smtplib.SMTPAuthenticationError:
        print("\n!!! ERRO DE AUTENTICAÇÃO SMTP: Verifique se EMAIL_USER e EMAIL_PASS estão corretos no seu .env. Lembre-se que EMAIL_PASS deve ser a Senha de App de 16 dígitos.\n")
    except Exception as e:
        print(f"\n!!! OCORREU UM ERRO INESPERADO AO ENVIAR O EMAIL: {e}\n")