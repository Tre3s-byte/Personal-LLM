import logging
import faiss
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class FaissVectorStore:
    def __init__(self, embedding_dim: int, index_path: str):
        self.embedding_dim = embedding_dim
        self.index_path = Path(index_path)
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            logger.info(f"FAISS index loaded from {self.index_path}")
        else:
            base = faiss.IndexFlatL2(embedding_dim)
            self.index = faiss.IndexIDMap(base)
            logger.info(f"FAISS index created new with dim={embedding_dim}")

    def add(self, embeddings: np.ndarray, ids: np.ndarray):
        embeddings = embeddings.astype("float32")
        faiss.normalize_L2(embeddings)
        self.index.add_with_ids(embeddings, ids.astype("int64"))
        logger.info(f"Added {len(embeddings)} embeddings to FAISS index")

    def save(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        logger.info(f"FAISS index saved at {self.index_path}")
