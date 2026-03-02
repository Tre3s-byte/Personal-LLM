"""FastAPI application bootstrap.

This module wires the API routers, logging configuration, database table
creation, and asynchronous RAG ingestion lifecycle.
"""

import os
import logging
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from app.routes import router as app_router
from api.routes import router as api_router
from utils.logging import setup_logging
from services.rag import LocalRAG, load_documents, chunk_text
from db.session import engine
from db.models import Base


# Initialize FastAPI app first
app = FastAPI(title="Local LLM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Include routers
app.include_router(app_router)
app.include_router(api_router)

# Initialize your RAG engine
rag_store: LocalRAG | None = None  # just declare, no instantiation

# --- Async background ingestion ---


async def async_ingest_and_index():
    """Build or load the retrieval index without blocking server startup."""
    global rag_store
    rag_store = LocalRAG()

    # Check if prebuilt index exists
    if os.path.exists(config.RAG_INDEX_PATH):
        logger.info("Loading existing RAG index...")
        await asyncio.to_thread(rag_store.load_index, config.RAG_INDEX_PATH)
        logger.info("RAG index loaded")
    else:
        logger.info("No existing index found, starting ingestion...")
        # Load documents in background thread
        documents = await asyncio.to_thread(load_documents)
        # Chunk documents
        chunks = []
        for doc in documents:
            chunks.extend(await asyncio.to_thread(chunk_text, doc))
        # Build FAISS index
        await asyncio.to_thread(rag_store.build_index, chunks)
        # Save index for next startup
        await asyncio.to_thread(rag_store.save_index, config.RAG_INDEX_PATH)
        logger.info("RAG ingestion and index build complete")


# Startup event must come after app is defined
@app.on_event("startup")
async def startup_event():
    """Create SQLAlchemy tables at startup if they do not exist yet."""
    Base.metadata.create_all(bind=engine)
    """Kick off background ingestion task once the server is running."""
    # Schedule background ingestion; server will start immediately
    asyncio.create_task(async_ingest_and_index())
    logger.info("Server started, RAG ingestion running in background")


@app.get("/query")
async def query_endpoint(q: str):
    """Query the in-memory RAG store once ingestion has completed."""
    global rag_store
    if not rag_store:
        return {"error": "RAG store not ready yet"}
    # Run retrieval in thread
    response = await asyncio.to_thread(rag_store.query, q)
    return {"query": q, "response": response}


# --- Health check ---
@app.get("/health")
async def health():
    """Liveness probe used by orchestrators and monitoring checks."""
    return {"status": "alive"}
