import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from functools import lru_cache
from typing import List, Dict, Any
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

@lru_cache(maxsize=1)
def get_embedding_model():
    """Carga el modelo de embeddings (singleton)"""
    logger.info("loading_embedding_model")
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

class VectorStoreService:
    """Servicio para gestionar ChromaDB"""
    
    def __init__(self):
        self.client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_function = get_embedding_model()
        logger.info("vector_store_initialized", 
                   host=settings.CHROMA_HOST, 
                   port=settings.CHROMA_PORT)
    
    def get_retriever(self, collection_name: str, k: int = 3):
        """Obtiene un retriever para una colección"""
        try:
            vector_store = Chroma(
                client=self.client,
                collection_name=collection_name,
                embedding_function=self.embedding_function,
            )
            return vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": k}
            )
        except Exception as e:
            logger.error("retriever_creation_failed", 
                        collection=collection_name, 
                        error=str(e))
            raise
    
    async def ingest_document(self, 
                            file_path: str, 
                            collection_name: str,
                            chunk_size: int = 1000,
                            chunk_overlap: int = 200) -> Dict[str, Any]:
        """Ingesta un documento en ChromaDB"""
        try:
            # Cargar documento según tipo
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith('.md'):
                loader = UnstructuredMarkdownLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_path}")
            
            documents = await loader.aload()
            
            # Dividir en chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            chunks = text_splitter.split_documents(documents)
            
            # Añadir metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "source": file_path,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
            
            # Crear o actualizar colección
            vector_store = Chroma(
                client=self.client,
                collection_name=collection_name,
                embedding_function=self.embedding_function
            )
            
            # Añadir documentos
            ids = await vector_store.aadd_documents(chunks)
            
            logger.info("document_ingested", 
                       file=file_path, 
                       collection=collection_name, 
                       chunks=len(chunks))
            
            return {
                "status": "success",
                "chunks_added": len(chunks),
                "collection": collection_name,
                "document_ids": ids
            }
            
        except Exception as e:
            logger.error("document_ingestion_failed", 
                        file=file_path, 
                        error=str(e))
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def search(self, 
                    query: str, 
                    collection_name: str, 
                    k: int = 3) -> List[Document]:
        """Busca documentos similares"""
        retriever = self.get_retriever(collection_name, k)
        return await retriever.aget_relevant_documents(query)

# Instancia global
vector_store_service = VectorStoreService()