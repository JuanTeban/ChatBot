from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Text, Integer
from datetime import datetime
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# URL de conexión para SQLite asíncrono
DATABASE_URL = f"sqlite+aiosqlite:///{settings.SQLITE_DB_PATH}"

# Motor de base de datos
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base para modelos
Base = declarative_base()

# Modelo para el historial de conversaciones
class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    message_type = Column(String, nullable=False)  # 'human' o 'ai'
    content = Column(Text, nullable=False)
    message_metadata = Column(Text)  # JSON string para metadata adicional
    created_at = Column(DateTime, default=datetime.utcnow)

async def init_db():
    """Inicializa la base de datos"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_initialized", path=settings.SQLITE_DB_PATH)

async def get_db():
    """Dependency para obtener sesión de DB"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()