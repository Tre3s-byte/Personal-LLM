# backend/services/rag/vector_manager.py
import logging
import numpy as np
from backend.services.embeddings import get_embedding_service
from backend.services.vector_store import FaissVectorStore
import backend.config as config

logger = logging.getLogger(__name__)


class LocalRAG:
    def __init__(self):
        self.embedder = get_embedding_service()
        test_vector = self.embedder.embed_texts(["dimension_check"])
        dim = len(test_vector[0])
        self.vector_store = FaissVectorStore(
            embedding_dim=dim,
            index_path=config.RAG_INDEX_PATH,
        )
        logger.info(f"Initialized LocalRAG with embedding dim={dim}")

    def add_vectors(self, chunks, embeddings, session, doc):
        from backend.model.models import Chunk

        for i, (chunk_text_value, emb) in enumerate(zip(chunks, embeddings)):
            chunk = Chunk(
                document_id=doc.id,
                chunk_index=i,
                text=chunk_text_value,
            )
            session.add(chunk)
            session.flush()
            self.vector_store.add(
                np.array([emb], dtype="float32"),
                np.array([chunk.id]),
            )
            chunk.vector_id = chunk.id
        logger.info(f"Added {len(chunks)} chunks for document {doc.id}")

    def search(self, query_emb, top_k: int = 4):
        ids = self.vector_store.search(query_emb, top_k)
        logger.info(f"Searched top {top_k} results in RAG index")
        return ids

    def save(self):
        self.vector_store.save()
        logger.info(f"RAG index saved at {config.RAG_INDEX_PATH}")
