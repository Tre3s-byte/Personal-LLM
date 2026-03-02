"""FastAPI application bootstrap.

This module wires the API routers, logging configuration, database table
creation, and asynchronous RAG ingestion lifecycle.
"""

import logging
import asyncio

from db.models import Base
from backend import config
from fastapi import FastAPI
from db.session import engine
from backend.services.rag import LocalRAG
from backend.utils.logging import setup_logging
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes import router as app_router
from backend.api.routes import router as api_router, set_rag_engine


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
rag_init_task: asyncio.Task | None = None

# --- Async background ingestion ---


async def async_sync_rag():
    global rag_store

    logger.info("Initializing RAG engine...")
    rag_store = LocalRAG()
    logger.info("Starting RAG sync process...")
    await asyncio.to_thread(rag_store.sync)
    logger.info("RAG sync completed")
    set_rag_engine(rag_store)


# Startup event must come after app is defined
@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

    global rag_init_task
    if rag_init_task is None or rag_init_task.done():
        rag_init_task = asyncio.create_task(async_sync_rag())

    logger.info("Server started, RAG sync running in background")


@app.get("/query")
async def query_endpoint(q: str):
    global rag_store

    if rag_store is None:
        return {"error": "RAG not initialized yet"}

    if rag_init_task and not rag_init_task.done():
        return {"error": "RAG still syncing"}

    response = await asyncio.to_thread(rag_store.search, q)
    return {"query": q, "response": response}


# --- Health check ---
@app.get("/health")
async def health():
    """Liveness probe used by orchestrators and monitoring checks."""
    return {"status": "alive"}
