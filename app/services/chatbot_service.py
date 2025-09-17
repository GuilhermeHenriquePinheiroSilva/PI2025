from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from typing import List, Dict, Any

class ChatbotService:
    """
    Encapsula a lógica para interagir com o modelo, incluindo a conversão do histórico.
    """
    def __init__(self, model_name: str = "phi4-mini"):
        # O resto do código permanece o mesmo. Apenas a importação acima mudou.
        self.model = ChatOllama(model=model_name)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", 
             """Você é um assistente de suporte ao cliente amigável e prestativo para a empresa GoGift
             A GoGift é um site de compra e venda de GiftCards (Cartões presente que te dão créditos de compra, acesso a um serviço), em que usuários podem comprar giftcards que outras empresas criaram
             dentro do próprio site GoGift.
             Seu objetivo é responder às perguntas dos usuários de forma clara, educada e concisa e em no máximo 150 caracteres, formule as resposta com bastante simplicidade no vocabulário 
             levando em consideração o contexto da conversa anterior."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_question}"),
        ])

        self.output_parser = StrOutputParser()
        self.chain = self.prompt | self.model | self.output_parser

    def _convert_history(self, history: List[Dict[str, Any]]):
        """Converte o histórico de dicionários para o formato de objetos do LangChain."""
        langchain_messages = []
        for msg in history:
            if msg.get("type") == "human":
                langchain_messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("type") == "ai":
                langchain_messages.append(AIMessage(content=msg.get("content", "")))
        return langchain_messages

    def get_response(self, user_question: str, history: List[Dict[str, Any]]) -> str:
        """
        Processa a pergunta do usuário, convertendo o histórico antes de invocar a cadeia.
        """
        chat_history = self._convert_history(history)

        try:
            response = self.chain.invoke({
                "chat_history": chat_history,
                "user_question": user_question,
            })
            return response
        except Exception as e:
            print(f"ERRO: Não foi possível obter resposta do modelo de linguagem: {e}")
            return "Desculpe, estou com dificuldades para processar sua mensagem no momento. Por favor, tente novamente."

# Instância única do serviço
chatbot_service = ChatbotService()