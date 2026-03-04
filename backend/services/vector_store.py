"""FAISS storage abstraction used by hybrid RAG."""

from __future__ import annotations

import logging
from pathlib import Path

import faiss
import numpy as np

logger = logging.getLogger("rag")


class FaissVectorStore:
    def __init__(self, embedding_dim: int, index_path: str):
        self.embedding_dim = embedding_dim
        self.index_path = Path(index_path)
        self.index = self._load_or_create_index()

    def _load_or_create_index(self):
        if self.index_path.exists():
            logger.info("faiss_index_loaded", extra={"extra_data": {"path": str(self.index_path)}})
            return faiss.read_index(str(self.index_path))
        base = faiss.IndexFlatIP(self.embedding_dim)
        logger.info("faiss_index_created", extra={"extra_data": {"dim": self.embedding_dim}})
        return faiss.IndexIDMap(base)

    def add(self, embeddings: np.ndarray, ids: np.ndarray) -> None:
        if embeddings.size == 0:
            return
        arr = embeddings.astype("float32")
        faiss.normalize_L2(arr)
        self.index.add_with_ids(arr, ids.astype("int64"))

    def search(self, embeddings: np.ndarray, top_k: int) -> list[int]:
        if self.index.ntotal == 0:
            return []
        arr = embeddings.astype("float32")
        faiss.normalize_L2(arr)
        _, ids = self.index.search(arr, top_k)
        return [int(v) for v in ids[0].tolist() if int(v) != -1]

    def remove(self, ids: np.ndarray) -> None:
        if ids.size:
            self.index.remove_ids(ids.astype("int64"))

    def save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
