from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json
from typing import AsyncGenerator

from src.api.schemas import (
    ChatRequest, ChatResponse, 
    DocumentUploadResponse, HealthResponse
)
import src.agents.support_graph as graph_module
from src.services.database import get_db, ConversationHistory
from src.services.vector_store import vector_store_service
from src.core.config import settings
from src.core.logging import get_logger
from langchain_core.messages import HumanMessage, AIMessage

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1")

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Endpoint principal del chat"""
    try:
        # Generar session_id si no existe
        session_id = request.session_id or f"session_{uuid.uuid4().hex}"
        
        # Configuración para el grafo
        config = {
            "configurable": {
                "thread_id": session_id,
                "checkpoint_ns": "support_agent"
            }
        }
        
        # Input para el grafo
        input_state = {
            "messages": [HumanMessage(content=request.message)],
            "session_id": session_id,
            "metadata": {"source": "api", "timestamp": str(datetime.utcnow())}
        }
        
        # Ejecutar grafo
        # Después
        result = await graph_module.support_agent_graph.ainvoke(input_state, config)
        
        # Extraer respuesta
        last_message = result["messages"][-1]
        response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # Guardar en base de datos
        # Guardar mensaje del usuario
        user_history = ConversationHistory(
            session_id=session_id,
            message_type="human",
            content=request.message,
            message_metadata=json.dumps({"intent": result.get("current_intent")})
        )
        db.add(user_history)
        
        # Guardar respuesta del bot
        bot_history = ConversationHistory(
            session_id=session_id,
            message_type="ai",
            content=response_text,
            message_metadata=json.dumps({
                "intent": result.get("current_intent"),
                "has_context": bool(result.get("rag_context"))
            })
        )
        db.add(bot_history)
        
        await db.commit()
        
        logger.info("chat_processed", 
                   session_id=session_id,
                   intent=result.get("current_intent"))
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            intent=result.get("current_intent"),
            metadata={
                "conversation_ended": result.get("conversation_ended", False),
                "email_collected": result.get("user_email") is not None
            }
        )
        
    except Exception as e:
        logger.error("chat_endpoint_error", error=str(e))
        raise HTTPException(status_code=500, detail="Error procesando mensaje")

@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Endpoint de chat con streaming"""
    session_id = request.session_id or f"session_{uuid.uuid4().hex}"
    
    async def generate() -> AsyncGenerator[str, None]:
        try:
            config = {
                "configurable": {
                    "thread_id": session_id,
                    "checkpoint_ns": "support_agent"
                }
            }
            
            input_state = {
                "messages": [HumanMessage(content=request.message)],
                "session_id": session_id,
                "metadata": {"source": "api_stream"}
            }
            
            # Stream eventos del grafo
            async with graph_module.support_agent_graph.astream_events(
                input_state, 
                config,
            ) as event_stream:
                async for event in event_stream:
                    if event["event"] == "on_chat_model_stream":
                        content = event["data"]["chunk"].content
                        if content:
                            yield f"data: {json.dumps({'chunk': content})}\n\n"
                    
                    elif event["event"] == "on_chat_model_end":
                        # Enviar metadata al final
                        metadata = {
                            "done": True,
                            "session_id": session_id
                        }
                        yield f"data: {json.dumps(metadata)}\n\n"
            
        except Exception as e:
            logger.error("stream_error", error=str(e))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection: str = settings.FAQ_COLLECTION
):
    """Carga un documento a la base de conocimiento"""
    try:
        # Validar tipo de archivo
        allowed_types = [".pdf", ".md"]
        file_ext = "." + file.filename.split(".")[-1].lower()
        
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no soportado. Use: {allowed_types}"
            )
        
        # Guardar temporalmente
        temp_path = f"/tmp/{uuid.uuid4()}{file_ext}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Ingestar documento
        result = await vector_store_service.ingest_document(
            file_path=temp_path,
            collection_name=collection
        )
        
        # Limpiar archivo temporal
        import os
        os.remove(temp_path)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return DocumentUploadResponse(
            status="success",
            message=f"Documento '{file.filename}' cargado exitosamente",
            document_id=str(uuid.uuid4()),
            chunks_created=result["chunks_added"]
        )
        
    except Exception as e:
        logger.error("document_upload_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check del sistema"""
    services_status = {}
    
    # Verificar ChromaDB
    try:
        vector_store_service.client.heartbeat()
        services_status["chromadb"] = "healthy"
    except:
        services_status["chromadb"] = "unhealthy"
    
    # Verificar Checkpointer
    services_status["checkpointer"] = "healthy" if checkpointer_service.checkpointer else "not_initialized"
    
    # Verificar Graph
    services_status["agent_graph"] = "healthy" if support_agent_graph else "not_initialized"
    
    return HealthResponse(
        status="healthy" if all(v == "healthy" for v in services_status.values()) else "degraded",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        services=services_status
    )