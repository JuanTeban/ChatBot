from langchain_core.language_models.chat_models import BaseChatModel
from langchain_cerebras import ChatCerebras
from src.core.config import settings
from src.core.logging import get_logger
from functools import lru_cache

logger = get_logger(__name__)

@lru_cache(maxsize=1)
def get_llm_provider(
    provider: str = "cerebras",
    model_name: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None
) -> BaseChatModel:
    """Factory para obtener instancia del LLM"""
    
    if provider == "cerebras":
        if not settings.CEREBRAS_API_KEY:
            raise ValueError("CEREBRAS_API_KEY not configured")
        
        # Configurar parámetros base
        base_params = {
            "model": model_name or settings.CEREBRAS_MODEL,
            "temperature": temperature or settings.CEREBRAS_TEMPERATURE,
            "max_tokens": max_tokens or settings.CEREBRAS_MAX_TOKENS,
            "api_key": settings.CEREBRAS_API_KEY,
            "streaming": True,
        }
        
        # Añadir optimizaciones específicas de Cerebras a model_kwargs
        base_params["model_kwargs"] = {
            "warm_tcp_connection": True,  # Reduce TTFT
        }
        
        model = ChatCerebras(**base_params)
        
        logger.info("llm_provider_created", 
                   provider=provider, 
                   model=model_name or settings.CEREBRAS_MODEL)
        
        return model
    
    else:
        raise ValueError(f"Provider '{provider}' not supported")