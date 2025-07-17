#!/usr/bin/env python
"""Script para ingestar documentos en la base de conocimiento"""

import asyncio
import argparse
from pathlib import Path
import sys

# Añadir src al path
sys.path.append(str(Path(__file__).parent.parent))

from src.services.vector_store import vector_store_service
from src.core.config import settings
from src.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

async def ingest_file(file_path: str, collection: str):
    """Ingesta un archivo"""
    logger.info("ingesting_file", file=file_path, collection=collection)
    
    result = await vector_store_service.ingest_document(
        file_path=file_path,
        collection_name=collection
    )
    
    if result["status"] == "success":
        logger.info("ingestion_complete", 
                   chunks=result["chunks_added"])
    else:
        logger.error("ingestion_failed", 
                    error=result["message"])

async def main():
    parser = argparse.ArgumentParser(
        description="Ingestar documentos en ChromaDB"
    )
    parser.add_argument(
        "files", 
        nargs="+", 
        help="Archivos a ingestar (PDF o Markdown)"
    )
    parser.add_argument(
        "--collection", 
        default=settings.FAQ_COLLECTION,
        help="Nombre de la colección"
    )
    
    args = parser.parse_args()
    
    for file_path in args.files:
        if not Path(file_path).exists():
            logger.error("file_not_found", file=file_path)
            continue
            
        await ingest_file(file_path, args.collection)

if __name__ == "__main__":
    asyncio.run(main())