from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from app.services.chatbot_service import chatbot_service

router = APIRouter(
    prefix="/chatbot",
    tags=["Chatbot"]
)

# O corpo da requisição agora espera uma lista de dicionários genéricos para o histórico
class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, Any]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    reply: str

@router.post("/ask", response_model=ChatResponse)
async def ask_chatbot(request: ChatRequest):
    """
    Recebe uma mensagem e o histórico da conversa, retorna a nova resposta da IA.
    """
    if not request.message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A mensagem não pode ser vazia."
        )
    
    # Passa a nova pergunta e o histórico (como lista de dicionários) diretamente para o serviço
    response_text = chatbot_service.get_response(request.message, request.history)
    
    return ChatResponse(reply=response_text)