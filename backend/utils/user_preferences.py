from backend.db.session import SessionLocal
from backend.db.queries.preferences import create_or_update_preference
from backend.services.embeddings import get_embedding_service


def save_preference(pref_type: str, content: str, importance: float = 0.0):
    session = SessionLocal()
    embedder = get_embedding_service()
    embedding = embedder.embed_texts([content])[0].tobytes()
    create_or_update_preference(session, pref_type, content, embedding, importance)
    session.close()
