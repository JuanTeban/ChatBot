from typing import Dict, Any
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from src.agents.state import AgentState
from src.agents.tools import (
    search_faq_knowledge, 
    redirect_to_faq_page,
    validate_email,
    initiate_agent_handoff
)
from src.llms.providers import get_llm_provider
from src.utils.prompts import (
    INTENT_CLASSIFIER_PROMPT,
    GREETING_RESPONSE,
    SUPPORT_AGENT_PROMPT,
    OUT_OF_SCOPE_RESPONSE,
    EMAIL_REQUEST,
    EMAIL_VALIDATION_ERROR
)
from src.core.logging import get_logger

logger = get_logger(__name__)

# LLM instance
llm = get_llm_provider("cerebras")

async def classify_intent_node(state: AgentState) -> Dict[str, Any]:
    """Clasifica la intención del mensaje del usuario"""
    try:
        # Obtener el último mensaje
        last_message = state["messages"][-1]
        if not isinstance(last_message, HumanMessage):
            return {}
        
        # Preparar historial reciente (últimos 4 mensajes)
        history = []
        for msg in state["messages"][-5:-1]:  # Excluye el mensaje actual
            role = "Usuario" if isinstance(msg, HumanMessage) else "Asistente"
            history.append(f"{role}: {msg.content[:100]}...")
        
        # Clasificar intención
        prompt = ChatPromptTemplate.from_template(INTENT_CLASSIFIER_PROMPT)
        chain = prompt | llm
        
        result = await chain.ainvoke({
            "history": "\n".join(history) if history else "Sin historial previo",
            "message": last_message.content
        })
        
        intent = result.content.strip().lower()
        
        # Validar intención
        valid_intents = ["greeting", "faq_request", "agent_request", 
                        "support_query", "out_of_scope"]
        if intent not in valid_intents:
            intent = "out_of_scope"
        
        logger.info("intent_classified", 
                   session_id=state["session_id"],
                   intent=intent)
        
        return {"current_intent": intent}
        
    except Exception as e:
        logger.error("intent_classification_failed", error=str(e))
        return {"current_intent": "out_of_scope"}

async def greeting_node(state: AgentState) -> Dict[str, Any]:
    """Maneja saludos"""
    return {
        "messages": [AIMessage(content=GREETING_RESPONSE)]
    }

async def faq_redirect_node(state: AgentState) -> Dict[str, Any]:
    """Redirige a FAQ"""
    response = redirect_to_faq_page()
    return {
        "messages": [AIMessage(content=response)]
    }

async def support_query_node(state: AgentState) -> Dict[str, Any]:
    """Maneja consultas de soporte usando RAG"""
    try:
        last_message = state["messages"][-1]
        query = last_message.content
        
        # Buscar en base de conocimiento
        context = await search_faq_knowledge.ainvoke({"query": query})
        
        # Si no hay contexto relevante
        if "No se encontró información" in context:
            response = (
                "No encontré información específica sobre tu consulta en nuestra "
                "base de conocimiento. Te sugiero:\n\n"
                "• Escribir **[FAQ]** para ver todas las preguntas frecuentes\n"
                "• Escribir **[Agente]** para hablar con un especialista"
            )
        else:
            # Generar respuesta basada en contexto
            prompt = ChatPromptTemplate.from_template(SUPPORT_AGENT_PROMPT)
            chain = prompt | llm
            
            result = await chain.ainvoke({
                "context": context,
                "question": query
            })
            response = result.content
        
        return {
            "messages": [AIMessage(content=response)],
            "rag_context": context
        }
        
    except Exception as e:
        logger.error("support_query_failed", error=str(e))
        return {
            "messages": [AIMessage(content=
                "Disculpa, tuve un problema al procesar tu consulta. "
                "Por favor, intenta nuevamente o escribe **[Agente]** para ayuda personalizada."
            )]
        }

async def request_email_node(state: AgentState) -> Dict[str, Any]:
    """Solicita email para transferencia"""
    return {
        "messages": [AIMessage(content=EMAIL_REQUEST)],
        "awaiting_email": True
    }

async def validate_email_node(state: AgentState) -> Dict[str, Any]:
    """Valida el email proporcionado"""
    try:
        last_message = state["messages"][-1]
        email_input = last_message.content.strip()
        
        # Validar email
        validation = await validate_email.ainvoke({"email": email_input})
        
        if validation["valid"]:
            # Email válido, proceder con handoff
            handoff_result = await initiate_agent_handoff.ainvoke({
                "email": validation["email"],
                "session_id": state["session_id"]
            })
            
            return {
                "messages": [AIMessage(content=handoff_result)],
                "user_email": validation["email"],
                "awaiting_email": False,
                "conversation_ended": True
            }
        else:
            # Email inválido
            return {
                "messages": [AIMessage(content=EMAIL_VALIDATION_ERROR)],
                "awaiting_email": True
            }
            
    except Exception as e:
        logger.error("email_validation_failed", error=str(e))
        return {
            "messages": [AIMessage(content=
                "Hubo un error al procesar tu email. Por favor, intenta nuevamente."
            )],
            "awaiting_email": True
        }

async def out_of_scope_node(state: AgentState) -> Dict[str, Any]:
    """Maneja consultas fuera de alcance"""
    return {
        "messages": [AIMessage(content=OUT_OF_SCOPE_RESPONSE)]
    }