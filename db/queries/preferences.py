from sqlalchemy import Session
from backend.model.models import Preferences
from sqlalchemy.sql import func


def get_preference(session: Session, pref_type: str):
    return session.query(Preferences).filter(Preferences.type == pref_type).first()


def create_or_update_preference(
    session: Session,
    pref_type,
    content: str,
    embedding: bytes = None,
    importance_score: float = 0.0,
):
    pref = get_preference(session, pref_type)
    if pref:
        pref.content = content
        pref.embeddings = embedding
        pref.importance_score = importance_score
    else:
        pref = Preferences(
            type=pref_type,
            content=content,
            embedding=embedding,
            importance_score=importance_score,
        )
        session.add(pref)
    session.commit()
    session.refresh(pref)
    return pref
