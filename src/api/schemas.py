from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    """Request para chat"""
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Mensaje del usuario"
    )
    session_id: Optional[str] = Field(
        None,
        description="ID de sesión para mantener contexto"
    )

class ChatResponse(BaseModel):
    """Response del chat"""
    response: str
    session_id: str
    intent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DocumentUploadResponse(BaseModel):
    """Response de carga de documento"""
    status: str
    message: str
    document_id: Optional[str] = None
    chunks_created: Optional[int] = None

class HealthResponse(BaseModel):
    """Response de health check"""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]