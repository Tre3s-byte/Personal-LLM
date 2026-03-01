from sentence_transformers import SentenceTransformer
import numpy as np

_embedding_service = None


class LocalEmbeddingService:
    def __init__(
        self, model_name="sentence-transformers/all-MiniLM-L6-v2", device=None
    ):
        self.model = SentenceTransformer(model_name, device=device)

    def embed_text(self, text: str) -> np.ndarray:
        embedding = self.model.encode(
            text, normalize_embeddings=True, convert_to_numpy=True
        )
        return embedding.reshape(1, -1)  # ensure 2D for FAISS

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(
            texts, normalize_embeddings=True, convert_to_numpy=True
        ).astype("float32")


def get_embedding_service():
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = LocalEmbeddingService(device="cuda")
        # change to device="cuda" if needed

    return _embedding_service
