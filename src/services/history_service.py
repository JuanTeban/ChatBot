from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import create_engine

from src.core.config import settings

# --- INICIO DE LA CORRECCIÓN ---
# Creamos un único motor de base de datos que se reutilizará.
# Es importante que el motor sea síncrono aquí, ya que la clase
# SQLChatMessageHistory lo gestiona internamente.
engine = create_async_engine(f"sqlite+aiosqlite:///{settings.SQLITE_DB_PATH}")
# --- FIN DE LA CORRECCIÓN ---

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Crea o recupera un historial de chat persistente para una sesión dada.
    """
    # --- INICIO DE LA CORRECCIÓN ---
    # Ya no usamos 'connection_string'. Ahora pasamos el motor directamente.
    # Esto es más eficiente y sigue las nuevas recomendaciones de LangChain.
    return SQLChatMessageHistory(
        session_id=session_id, 
        connection=engine,
        async_mode=True
    )
    # --- FIN DE LA CORRECCIÓN ---
