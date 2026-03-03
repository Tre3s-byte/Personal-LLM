import faiss
import numpy as np
from backend.services.embeddings import get_embedding_service
from backend.services.vector_store import FaissVectorStore
import backend.config as config


class LocalRAG:
    def __init__(self):
        self.embedder = get_embedding_service()
        # Determine embedding dimension once
        test_vector = self.embedder.embed_texts(["dimension_check"])
        dim = len(test_vector[0])

        self.vector_store = FaissVectorStore(
            embedding_dim=dim,
            index_path=config.RAG_INDEX_PATH,
        )

    def _ensure_vector_store(self, dim: int):
        if self.vector_store is None:
            self.vector_store = FaissVectorStore(
                embedding_dim=dim,
                index_path=config.RAG_INDEX_PATH,
            )

    def add_vectors(self, chunks, embeddings, session, doc):
        import numpy as np

        for i, (chunk_text_value, emb) in enumerate(zip(chunks, embeddings)):
            from backend.model.models import Chunk

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

    def search(self, query_emb, top_k: int = 4):
        ids = self.vector_store.search(query_emb, top_k)
        return ids

    def save(self):
        self.vector_store.save()
