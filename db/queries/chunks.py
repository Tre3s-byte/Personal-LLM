from sqlalchemy.orm import Session
from backend.model.models import Document, Chunk


def get_document_by_path(session: Session, path: str):
    return session.query(Document).filter(Document.path == path).first()


def create_document(
    session: Session, path: str, checksum=None, mtime=None, namespace=None
):
    doc = Document(path=path, checksum=checksum, mtime=mtime, namespace=namespace)
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def add_chunk(session: Session, document_id: int, chunk_index: int, text: str):
    chunk = Chunk(document_id=document_id, chunk_index=chunk_index, text=text)
    session.add(chunk)
    session.commit()
    session.refresh(chunk)
    return chunk
