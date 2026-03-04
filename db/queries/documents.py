from __future__ import annotations

from sqlalchemy.orm import Session

from backend.model.models import Document


def get_document_by_path(session: Session, path: str) -> Document | None:
    return session.query(Document).filter(Document.path == path).first()


def create_document(session: Session, path: str, checksum: str | None = None, mtime: str | None = None, namespace: str | None = None) -> Document:
    doc = Document(path=path, checksum=checksum, mtime=mtime, namespace=namespace)
    session.add(doc)
    session.flush()
    return doc
