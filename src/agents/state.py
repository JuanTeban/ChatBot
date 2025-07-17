from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """Estado del agente de soporte"""
    messages: Annotated[List[BaseMessage], operator.add]
    session_id: str
    current_intent: Optional[str]
    user_email: Optional[str]
    rag_context: Optional[str]
    awaiting_email: bool
    conversation_ended: bool
    metadata: Dict[str, Any]