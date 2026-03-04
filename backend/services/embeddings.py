from typing import Union, List
import numpy as np

_embedding_service = None


class LocalEmbeddingService:
    def __init__(
        self, model_name="sentence-transformers/all-MiniLM-L6-v2", device=None
    ):
        self.model_name = model_name
        self.device = device
        self.model = None

    def _load_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.model_name, device=self.device)

    def embed_text(self, text: str) -> np.ndarray:
        self._load_model()
        embedding = self.model.encode(
            text, normalize_embeddings=True, convert_to_numpy=True
        )
        return embedding.reshape(1, -1)

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        self._load_model()
        return self.model.encode(
            texts, normalize_embeddings=True, convert_to_numpy=True
        ).astype("float32")


def get_embedding_service() -> LocalEmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = LocalEmbeddingService(device="cuda")
    return _embedding_service
