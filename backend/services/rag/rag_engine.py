from backend.db.session import SessionLocal
from backend.db.queries.documents import create_document, add_chunk
from backend.services.rag.vector_manager import LocalRAG
from backend.services.rag.document_loader import load_documents, chunk_text
from backend.services.embeddings import get_embedding_service
import numpy as np
from pathlib import Path
import backend.config as config


def build_rag_index(batch_size: int = 5000):
    Path(config.RAG_INDEX_PATH).unlink(missing_ok=True)
    Path(config.RAG_INDEX_PATH + ".docs").unlink(missing_ok=True)

    rag = LocalRAG()
    raw_docs = load_documents()

    all_chunks = []
    doc_map = {}

    session = SessionLocal()

    embedder = get_embedding_service()
    embeddings_list = []

    for text in raw_docs:
        doc = create_document(
            session, path="unknown_path"
        )  # Optionally add real paths/checksums
        chunks = chunk_text(text)
        doc_map[doc.id] = chunks

        for i, chunk_text_value in enumerate(chunks):
            chunk = add_chunk(
                session, document_id=doc.id, chunk_index=i, text=chunk_text_value
            )
            emb = embedder.embed_texts([chunk_text_value])[0]
            embeddings_list.append(emb)
            rag.vector_store.add(np.array([emb], dtype="float32"), np.array([chunk.id]))

    rag.vector_store.save()
    print(f"[SAVE] Index saved at {config.RAG_INDEX_PATH}")
    session.close()
    return rag
