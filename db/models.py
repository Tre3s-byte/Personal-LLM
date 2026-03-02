from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from session import Base


class Document(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True, index=True, nullable=True)
    checksum = Column(String, nullable=True)
    mtime = Column(String, nullable=True)
    namespace = Column(String, default=False)

    chunks = relationship("Chunk", back_populates="file")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("files.id"))
    chunk_index = Column(Integer)
    text = Column(Text)
    vector_id = Column(Integer, unique=True)
    embedding_model_version = Column(String)
    deleted = Column(Boolean, default=False)
    document = relationship("Document", back_populates="chunks")
