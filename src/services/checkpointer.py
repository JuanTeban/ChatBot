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
            # Simplemente creamos la instancia. No llamamos a .setup()
            self.checkpointer = AsyncSqliteSaver.from_conn_string(
                f"sqlite+aiosqlite:///{self.db_path}"
            )
            logger.info("checkpointer_initialized", path=self.db_path)
        except Exception as e:
            logger.error("checkpointer_init_failed", error=str(e))
            raise

    async def close(self):
        """Cierra la conexión del checkpointer (gestionado por el grafo ahora)"""
        # El grafo se encarga de cerrar la conexión, así que no hacemos nada aquí.
        logger.info("checkpointer_closed (managed by graph)")
        pass

    def get_checkpointer(self):
        """Retorna el checkpointer"""
        if not self.checkpointer:
            raise RuntimeError("Checkpointer not initialized")
        return self.checkpointer

# Instancia global
checkpointer_service = CheckpointerService()