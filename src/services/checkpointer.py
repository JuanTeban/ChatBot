from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from src.core.config import settings
from src.core.logging import get_logger
import os

logger = get_logger(__name__)

class CheckpointerService:
    """Servicio para gestionar el checkpointer de LangGraph"""

    def __init__(self):
        self.checkpointer = None
        self.db_path = os.path.join(
            os.path.dirname(settings.SQLITE_DB_PATH),
            "checkpoints.db"
        )

    async def initialize(self):
        """Inicializa el checkpointer"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Crear la instancia del checkpointer
            conn_string = f"sqlite+aiosqlite:///{self.db_path}"
            self.checkpointer = AsyncSqliteSaver.from_conn_string(conn_string)
            
            logger.info("checkpointer_initialized", path=self.db_path)
        except Exception as e:
            logger.error("checkpointer_init_failed", error=str(e))
            raise

    async def close(self):
        """Cierra la conexión del checkpointer"""
        if self.checkpointer:
            try:
                await self.checkpointer.close()
                logger.info("checkpointer_closed")
            except Exception as e:
                logger.error("checkpointer_close_failed", error=str(e))

    def get_checkpointer(self):
        """Retorna el checkpointer"""
        if not self.checkpointer:
            raise RuntimeError("Checkpointer not initialized")
        return self.checkpointer

# Instancia global
checkpointer_service = CheckpointerService()