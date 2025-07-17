from langchain.tools import tool
from src.services.vector_store import vector_store_service
from src.core.config import settings
from src.core.logging import get_logger
import re
import random

logger = get_logger(__name__)

@tool
async def search_faq_knowledge(query: str) -> str:
    """Busca en la base de conocimiento de preguntas frecuentes"""
    try:
        # Usar el método search del vector_store_service
        documents = await vector_store_service.search(
            query=query,
            collection_name=settings.FAQ_COLLECTION,
            k=3
        )
        
        if not documents:
            return "No se encontró información relevante sobre esta consulta."
        
        # Formatear contexto
        context_parts = []
        for i, doc in enumerate(documents, 1):
            content = doc.page_content.strip()
            source = doc.metadata.get('source', 'Unknown')
            context_parts.append(f"[Fuente {i}: {source}]\n{content}")
        
        return "\n\n---\n\n".join(context_parts)
        
    except Exception as e:
        logger.error("faq_search_failed", query=query, error=str(e))
        return "Error al buscar en la base de conocimiento."

@tool
def redirect_to_faq_page() -> str:
    """Redirige a la página de preguntas frecuentes"""
    return (
        "📋 Puedes encontrar respuestas a las preguntas más comunes en nuestra "
        "[página de FAQ](https://support.example.com/faq).\n\n"
        "Si no encuentras lo que buscas, escribe **[Agente]** para hablar con una persona."
    )

@tool
def validate_email(email: str) -> dict:
    """Valida el formato de un email"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    is_valid = bool(re.match(email_pattern, email.strip(), re.IGNORECASE))
    
    return {
        "valid": is_valid,
        "email": email.strip() if is_valid else None,
        "message": "Email válido" if is_valid else "Formato de email inválido"
    }

@tool
def initiate_agent_handoff(email: str, session_id: str) -> str:
    """Inicia la transferencia a un agente humano"""
    # Simular disponibilidad (en producción, consultar sistema real)
    agent_available = random.choice([True, False])
    
    logger.info("agent_handoff_initiated", 
               email=email, 
               session_id=session_id,
               available=agent_available)
    
    if agent_available:
        return (
            f"✅ **Transferencia exitosa**\n\n"
            f"Un agente se pondrá en contacto contigo en breve a: {email}\n"
            f"Tu número de ticket es: #{session_id[:8].upper()}\n\n"
            f"¡Gracias por contactarnos!"
        )
    else:
        return (
            f"⏳ **Todos nuestros agentes están ocupados**\n\n"
            f"Hemos registrado tu solicitud y te contactaremos a: {email}\n"
            f"Tu número de ticket es: #{session_id[:8].upper()}\n"
            f"Tiempo estimado de respuesta: 2-4 horas\n\n"
            f"¡Gracias por tu paciencia!"
        )