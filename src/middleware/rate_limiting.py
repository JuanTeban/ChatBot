from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para rate limiting"""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(list)
        self.daily_tokens = defaultdict(int)
        self.lock = asyncio.Lock()
    
    async def dispatch(self, request: Request, call_next):
        # Solo aplicar a endpoints de API
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        
        # Obtener identificador (por ahora, IP)
        client_id = request.client.host if request.client else "unknown"
        
        async with self.lock:
            # Limpiar requests antiguos
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > minute_ago
            ]
            
            # Verificar límite por minuto
            if len(self.requests[client_id]) >= settings.RATE_LIMIT_REQUESTS_PER_MINUTE:
                logger.warning("rate_limit_exceeded", client_id=client_id)
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please try again later."
                )
            
            # Registrar request
            self.requests[client_id].append(now)
        
        # Procesar request
        response: Response = await call_next(request)
        
        # Extraer headers de Cerebras si existen
        if "x-ratelimit-remaining" in response.headers:
            remaining = response.headers.get("x-ratelimit-remaining")
            reset_time = response.headers.get("x-ratelimit-reset")
            
            logger.info("cerebras_rate_limit_status",
                       client_id=client_id,
                       remaining=remaining,
                       reset_time=reset_time)
            
            # Si estamos cerca del límite, añadir warning
            if remaining and int(remaining) < 100:
                response.headers["X-Warning"] = "Approaching API rate limit"
        
        return response

class TokenUsageMiddleware(BaseHTTPMiddleware):
    """Middleware para tracking de uso de tokens"""
    
    async def dispatch(self, request: Request, call_next):
        # Añadir tracking de tokens aquí si es necesario
        response = await call_next(request)
        return response