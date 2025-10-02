from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
# --- ALTERAÇÃO 1: Importando a função correta 'verify_token' ---
from app.auth.jwt_handler import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_admin(token: str = Depends(oauth2_scheme)):
    """
    Dependência para verificar se o usuário é um admin.
    Decodifica o token, verifica a role e retorna os dados do usuário.
    Levanta HTTPException se o token for inválido ou o usuário não for admin.
    """
    try:
        payload = decode_access_token(token) 
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if payload.get("role").lower() != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: Requer privilégios de administrador",
            )
            
        return payload
    except (JWTError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível validar as credenciais",
            headers={"WWW-Authenticate": "Bearer"},
        )