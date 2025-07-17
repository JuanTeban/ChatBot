import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

BASE_DIR = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, '.env'),
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    # API Keys
    CEREBRAS_API_KEY: str
    OPENAI_API_KEY: Optional[str] = None
    
    # Cerebras Config
    CEREBRAS_MODEL: str = "llama-3.3-70b"
    CEREBRAS_MAX_TOKENS: int = 2048
    CEREBRAS_TEMPERATURE: float = 0.1
    
    # Database
    SQLITE_DB_PATH: str = os.path.join(BASE_DIR, 'data', 'sqlite', 'sessions.db')
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8081
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 50
    RATE_LIMIT_TOKENS_PER_DAY: int = 900000
    
    # Application
    APP_NAME: str = "Support Agent"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # ChromaDB Collections
    FAQ_COLLECTION: str = "faq_knowledge"
    DOCUMENTS_COLLECTION: str = "user_documents"

settings = Settings()