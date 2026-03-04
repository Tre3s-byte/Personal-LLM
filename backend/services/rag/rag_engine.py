from backend.db.session import SessionLocal
from backend.db.queries.documents import create_document, add_chunk
from backend.services.rag.vector_manager import LocalRAG
from backend.services.rag.document_loader import load_documents, chunk_text
from backend.services.embeddings import get_embedding_service
import numpy as np
from pathlib import Path
import backend.config as config
import logging

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def build_rag_index(batch_size: int = 5000):
    # Remove old index files
    Path(config.RAG_INDEX_PATH).unlink(missing_ok=True)
    Path(config.RAG_INDEX_PATH + ".docs").unlink(missing_ok=True)
    logger.info(f"Old FAISS index files removed: {config.RAG_INDEX_PATH}")

    rag = LocalRAG()
    raw_docs = load_documents()
    logger.info(f"Loaded {len(raw_docs)} documents for indexing")

    doc_map = {}
    session = SessionLocal()
    embedder = get_embedding_service()
    embeddings_list = []

    for doc_idx, text in enumerate(raw_docs, start=1):
        doc = create_document(session, path="unknown_path")
        chunks = chunk_text(text)
        doc_map[doc.id] = chunks
        logger.info(f"Document {doc_idx} (id={doc.id}) split into {len(chunks)} chunks")

        for i, chunk_text_value in enumerate(chunks):
            chunk = add_chunk(
                session, document_id=doc.id, chunk_index=i, text=chunk_text_value
            )
            emb = embedder.embed_texts([chunk_text_value])[0]
            embeddings_list.append(emb)
            rag.vector_store.add(np.array([emb], dtype="float32"), np.array([chunk.id]))
            logger.debug(f"Chunk {i} of doc {doc.id} indexed with vector id {chunk.id}")

    rag.vector_store.save()
    logger.info(f"FAISS index saved at {config.RAG_INDEX_PATH}")
    session.close()
    return rag
