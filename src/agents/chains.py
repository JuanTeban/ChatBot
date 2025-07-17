# src/agents/chains.py

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.retry import RunnableRetry
from src.llms.providers import get_llm_provider
from src.services.vector_store import get_retriever
from src.services.history_service import get_session_history
from operator import itemgetter
from langchain_core.runnables.history import RunnableWithMessageHistory


def create_chat_chain(
    provider: str = "cerebras",
    model_name: str | None = None,
    temperature: float = 0.0
) -> Runnable:
    """
    Crea y devuelve una cadena de chat simple (prompt → LLM → parser)
    con reintentos y timeout configurados.
    """
    # 1) Plantilla de prompt
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "Eres un asistente virtual experto. Responde de forma clara y concisa."),
        ("human", "{question}")
    ])

    # 2) Instancia del LLM
    llm = get_llm_provider(provider=provider, model_name=model_name, temperature=temperature)

    # 3) Parser de salida
    output_parser = StrOutputParser()

    # 4) Cadena base: prompt → llm → parser
    base_chain = prompt_template | llm | output_parser

    # 5) Añadir retry y timeout
    chain = (
        base_chain
        .with_retry(max_retries=3, backoff="exponential")
        .with_config(timeout=60)
    )
    return chain


def create_rag_chain(collection_name: str) -> Runnable:
    """
    Crea y devuelve una cadena RAG (Retrieval-Augmented Generation)
    que primero recupera contexto de ChromaDB y luego genera respuesta,
    con reintentos y timeout configurados.
    """
    # 1) Retriever de la colección
    retriever = get_retriever(collection_name)

    # 2) Prompt para RAG
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "Eres un asistente experto que responde SOLO con el contexto. "
                   "Si no está en el contexto, di 'No tengo información suficiente'.\n\n"
                   "Contexto:\n{context}"),
        ("human", "Pregunta: {question}")
    ])

    # 3) LLM
    llm = get_llm_provider("cerebras")

    # 4) Formateo de documentos recuperados
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # 5) Cadena base: asignar context → prompt → llm → parser
    base_rag = (
        RunnablePassthrough.assign(
            context=itemgetter("question") | retriever | format_docs
        )
        | prompt_template
        | llm
        | StrOutputParser()
    )

    # 6) Añadir retry y timeout
    rag_chain = (
        base_rag
        .with_retry(max_retries=3, backoff="exponential")
        .with_config(timeout=60)
    )
    return rag_chain


def create_conversational_chain() -> Runnable:
    """
    Crea una cadena conversacional con historial persistente,
    reintentos y timeout configurados.
    """
    # 1) LLM
    llm = get_llm_provider("cerebras")

    # 2) Prompt con placeholder de historial
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "Eres un asistente conversacional muy útil. "
                   "Usa el historial si es relevante."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])

    # 3) Cadena base
    base_chain = prompt_template | llm | StrOutputParser()

    # 4) Proteger con retry y timeout
    safe_chain = (
        base_chain
        .with_retry(max_retries=3, backoff="exponential")
        .with_config(timeout=60)
    )

    # 5) Envolver con gestor de historial
    chain_with_history = RunnableWithMessageHistory(
        safe_chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="history",
    )
    return chain_with_history


# Instancias listas para importar
basic_chat_chain: Runnable = create_chat_chain()
rag_chain_factory = create_rag_chain  # úsalo como create_rag_chain("tu_colección")
conversational_chain: Runnable = create_conversational_chain()
