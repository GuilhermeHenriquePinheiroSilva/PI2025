from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
from typing import Dict

# Carrega as variáveis de ambiente do seu arquivo .env
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
# É uma boa prática ter um tempo de expiração maior para testes
ACCESS_TOKEN_EXPIRE_MINUTES = 30 

def create_access_token(data: Dict, expires_delta: timedelta | None = None):
    """
    Cria um novo token de acesso JWT.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Usa o tempo de expiração padrão se nenhum for fornecido
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict | None:
    """
    Verifica e decodifica um token JWT.
    Retorna o payload (os dados) se o token for válido, ou None se for inválido.
    """
    try:
        # Tenta decodificar o token usando a chave secreta e o algoritmo
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # Se ocorrer qualquer erro (token expirado, assinatura inválida, etc.), retorna None
        return None
    
def create_email_verification_token(user_id: str, expires_minutes: int = 60):
    """
    Cria um token JWT para verificação de email.
    """
    expire = timedelta(minutes=expires_minutes)
    data = {
        "sub": user_id,  # identifica o usuário
        "purpose": "email_verification"
    }
    return create_access_token(data, expires_delta=expire)


def verify_email_verification_token(token: str) -> str | None:
    """
    Verifica um token de verificação de email e retorna o user_id se for válido.
    """
    payload = verify_token(token)
    if payload and payload.get("purpose") == "email_verification":
        return payload.get("sub")  # retorna o id do usuário
    return None