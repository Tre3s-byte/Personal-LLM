from __future__ import annotations

from sqlalchemy.orm import Session

from backend.model.models import Chunk


def add_chunk(session: Session, document_id: int, chunk_index: int, text: str) -> Chunk:
    chunk = Chunk(document_id=document_id, chunk_index=chunk_index, text=text)
    session.add(chunk)
    session.flush()
    return chunk
