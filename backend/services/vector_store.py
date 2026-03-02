"""Minimal FAISS vector-store wrapper for text chunk retrieval."""

import faiss
import numpy as np
from pathlib import Path


class FaissVectorStore:
    def __init__(self, embedding_dim: int, index_path: str):
        self.embedding_dim = embedding_dim
        self.index_path = Path(index_path)

        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        else:
            base = faiss.IndexFlatL2(embedding_dim)
            self.index = faiss.IndexIDMap(base)

    def add(self, embeddings: np.ndarray, ids: np.ndarray):
        embeddings = embeddings.astype("float32")
        faiss.normalize_L2(embeddings)
        self.index.add_with_ids(embeddings, ids.astype("int64"))

    def remove(self, ids: np.ndarray):
        self.index.remove_ids(ids.astype("int64"))

    def search(self, query_embedding: np.ndarray, k: int = 5):
        query_embedding = query_embedding.astype("float32")
        faiss.normalize_L2(query_embedding)
        distances, ids = self.index.search(query_embedding, k)
        return ids[0]

    def save(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
