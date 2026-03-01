import faiss
import numpy as np
from typing import List


class FaissVectorStore:
    def __init__(self, embedding_dim: int):
        self.embedding_dim = embedding_dim
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.texts = []

    def add(self, embeddings: np.ndarray, texts: List[str]):
        """
        embeddings: shape (n, dim)
        texts: list of original text chunks
        """
        if not isinstance(embeddings, np.ndarray):
            embeddings = np.array(embeddings)

        self.index.add(embeddings.astype("float32"))
        self.texts.extend(texts)

    def search(self, query_embedding: np.ndarray, k: int = 5):
        """
        Query embedding:shape(1,dim)
        """
        if not isinstance(query_embedding, np.ndarray):
            query_embedding = np.ndarray(query_embedding)

        distances, indices = self.index.search(query_embedding.astype("float32"), k)

        results = []
        for idx in indices[0]:
            if idx < len(self.texts):
                results.append(self.texts[idx])
        return results
