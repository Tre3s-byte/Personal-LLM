"""SQLAlchemy metadata models for documents and embedded chunks."""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .session import Base


class Document(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True, index=True, nullable=False)
    checksum = Column(String, nullable=True)
    mtime = Column(String, nullable=True)
    namespace = Column(String, nullable=True)

    chunks = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"))
    chunk_index = Column(Integer)
    text = Column(Text)
    vector_id = Column(Integer, unique=True, index=True)
    embedding_model_version = Column(String)
    deleted = Column(Boolean, default=False)

    document = relationship("Document", back_populates="chunks")
