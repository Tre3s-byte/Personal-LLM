from pathlib import Path
import numpy as np
import faiss
from backend.services.rag.vector_manager import LocalRAG
from backend.services.rag.document_loader import load_documents, chunk_text
from backend.services.embeddings import get_embedding_service
import backend.config as config


def build_rag_index(batch_size: int = 5000) -> LocalRAG:
    # Remove old index if exists
    Path(config.RAG_INDEX_PATH).unlink(missing_ok=True)
    Path(config.RAG_INDEX_PATH + ".docs").unlink(missing_ok=True)

    rag = LocalRAG()
    raw_docs = load_documents()

    all_chunks = []
    for doc in raw_docs:
        all_chunks.extend(chunk_text(doc))

    if not all_chunks:
        raise ValueError("No documents found for indexing")

    embedder = get_embedding_service()
    embeddings_list = []

    print(
        f"[BUILD] Total chunks: {len(all_chunks)}, processing in batches of {batch_size}..."
    )

    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        batch_emb = embedder.embed_texts(batch)
        embeddings_list.append(batch_emb)

    embeddings = np.vstack(embeddings_list).astype("float32")
    faiss.normalize_L2(embeddings)

    dims = embeddings.shape[1]
    print(f"[BUILD] Embedding dims: {dims}, total vectors: {embeddings.shape[0]}")

    rag.vector_store.index = faiss.IndexFlatL2(dims)
    rag.vector_store.index.add(embeddings)
    rag.vector_store.save()
    print(f"[SAVE] Index saved at {config.RAG_INDEX_PATH}")

    return rag
