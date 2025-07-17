from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from src.core.config import settings
import os

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Crea o recupera un historial de chat persistente para una sesión dada.
    """
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(settings.SQLITE_DB_PATH), exist_ok=True)
    
    return SQLChatMessageHistory(
        session_id=session_id,
        connection_string=f"sqlite:///{settings.SQLITE_DB_PATH}"
    )