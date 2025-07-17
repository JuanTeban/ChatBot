from langgraph.graph import StateGraph, END
from src.agents.state import AgentState
from src.agents import nodes
from src.services.checkpointer import checkpointer_service
from src.core.logging import get_logger

logger = get_logger(__name__)

def route_after_intent(state: AgentState) -> str:
    """Enruta basado en la intención clasificada"""
    intent = state.get("current_intent")
    
    # Si estamos esperando email, validar
    if state.get("awaiting_email", False):
        return "validate_email"
    
    # Si la conversación terminó, finalizar
    if state.get("conversation_ended", False):
        return END
    
    # Enrutar según intención
    routing = {
        "greeting": "greeting",
        "faq_request": "faq_redirect",
        "agent_request": "request_email",
        "support_query": "support_query",
        "out_of_scope": "out_of_scope"
    }
    
    return routing.get(intent, "out_of_scope")

def should_end(state: AgentState) -> str:
    """Determina si la conversación debe terminar"""
    if state.get("conversation_ended", False):
        return END
    return "classify_intent"

def create_support_graph():
    """Crea el grafo del agente de soporte"""
    try:
        # Crear grafo
        graph = StateGraph(AgentState)
        
        # Añadir nodos
        graph.add_node("classify_intent", nodes.classify_intent_node)
        graph.add_node("greeting", nodes.greeting_node)
        graph.add_node("faq_redirect", nodes.faq_redirect_node)
        graph.add_node("support_query", nodes.support_query_node)
        graph.add_node("request_email", nodes.request_email_node)
        graph.add_node("validate_email", nodes.validate_email_node)
        graph.add_node("out_of_scope", nodes.out_of_scope_node)
        
        # Definir flujo
        graph.set_entry_point("classify_intent")
        
        # Enrutamiento condicional después de clasificar
        graph.add_conditional_edges(
            "classify_intent",
            route_after_intent
        )
        
        # Edges de retorno a clasificación
        for node in ["greeting", "faq_redirect", "support_query", "out_of_scope"]:
            graph.add_conditional_edges(node, should_end)
        
        # Email flow
        graph.add_edge("request_email", "classify_intent")
        graph.add_conditional_edges("validate_email", should_end)
        
        # Compilar con checkpointer
        checkpointer = checkpointer_service.get_checkpointer()
        compiled_graph = graph.compile(checkpointer=checkpointer)
        
        logger.info("support_graph_created")
        return compiled_graph
        
    except Exception as e:
        logger.error("graph_creation_failed", error=str(e))
        raise

# Variable global para el grafo (se inicializa en startup)
support_agent_graph = None