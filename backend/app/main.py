import logging
from fastapi import FastAPI
from app.routes import router as app_router
from api.routes import router as api_router
from utils.logging import setup_logging
from services.rag import LocalRAG, load_documents, chunk_text

# Initialize FastAPI app first
app = FastAPI(title="Local LLM API")

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Include routers
app.include_router(app_router)
app.include_router(api_router)

# Initialize your RAG engine
rag = LocalRAG()


# Startup event must come after app is defined
@app.on_event("startup")
def startup_event():
    documents = load_documents()
    print("Loaded documents:", documents)
    chunks = [chunk for doc in documents for chunk in chunk_text(doc)]
    rag.build_index(chunks)
