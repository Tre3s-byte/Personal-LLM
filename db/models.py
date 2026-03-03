"""SQLAlchemy metadata models for documents and embedded chunks."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    Float,
    DateTime,
    LargeBinary,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .session import Base


class Document(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True, nullable=False, index=True)
    checksum = Column(String, nullable=True)
    mtime = Column(String, nullable=True)
    namespace = Column(String, index=True, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    chunks = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer,
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    vector_id = Column(Integer, unique=True, index=True, nullable=True)
    embedding_model_version = Column(String, nullable=True)

    deleted = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, server_default=func.now())

    document = relationship("Document", back_populates="chunks")


class Preferences(Base):
    __tablename__ = "personal_preferences"

    id = Column(Integer, primary_key=True, index=True)

    type = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)

    embedding = Column(LargeBinary, nullable=True)

    importance_score = Column(Float, default=0.0)

    created_at = Column(DateTime, server_default=func.now())
    last_access = Column(DateTime, onupdate=func.now())

    access_count = Column(Integer, default=0)
