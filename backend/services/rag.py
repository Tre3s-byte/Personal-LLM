"""Retrieval-Augmented Generation primitives and document ingestion pipeline."""

import re
import os
import faiss
import logging
import hashlib

import numpy as np
from typing import List
from pathlib import Path
from PyPDF2 import PdfReader


import backend.config as config
from db.session import SessionLocal
from sqlalchemy.orm import Session
from db.models import Document, Chunk
from .vector_store import FaissVectorStore
from .embeddings import get_embedding_service


class LocalRAG:
    def __init__(self):
        self.embedder = get_embedding_service()

        # Determine embedding dimension once
        test_vector = self.embedder.embed_texts(["dimension_check"])
        dim = len(test_vector[0])

        self.vector_store = FaissVectorStore(
            embedding_dim=dim,
            index_path=config.RAG_INDEX_PATH,
        )

    def _ensure_vector_store(self, dim: int):
        if self.vector_store is None:
            self.vector_store = FaissVectorStore(
                embedding_dim=dim,
                index_path=config.RAG_INDEX_PATH,
            )

    def _checksum(self, path: Path):
        return hashlib.md5(path.read_bytes()).hexdigest()

    def sync(self):
        session: Session = SessionLocal()

        for base_path in config.RAG_PATHS:
            for file in base_path.rglob("*"):
                if not file.is_file():
                    continue

                checksum = self._checksum(file)
                mtime = str(file.stat().st_mtime)

                doc = session.query(Document).filter(Document.path == str(file)).first()

                if doc and doc.checksum == checksum:
                    continue

                if doc:
                    self._delete_document_chunks(session, doc)

                text = file.read_text(encoding="utf-8", errors="ignore")
                doc = Document(
                    path=str(file),
                    checksum=checksum,
                    mtime=mtime,
                )
                session.add(doc)
                session.flush()

                chunks = chunk_text(text)

                embeddings = self.embedder.embed_texts(chunks)
                embeddings = np.array(embeddings, dtype="float32")

                self._ensure_vector_store(embeddings.shape[1])

                for i, (chunk_text_value, emb) in enumerate(zip(chunks, embeddings)):
                    chunk = Chunk(
                        document_id=doc.id,
                        chunk_index=i,
                        text=chunk_text_value,
                    )
                    session.add(chunk)
                    session.flush()

                    self.vector_store.add(
                        np.array([emb]),
                        np.array([chunk.id]),
                    )

                    chunk.vector_id = chunk.id

        session.commit()
        self.vector_store.save()
        session.close()

    def _delete_document_chunks(self, session, doc):
        ids = [c.vector_id for c in doc.chunks if c.vector_id is not None]
        if ids:
            self.vector_store.remove(np.array(ids))

        session.delete(doc)

    def search(self, query: str, top_k: int = 4):
        session = SessionLocal()

        query_emb = self.embedder.embed_texts([query])
        query_emb = np.array(query_emb, dtype="float32")

        ids = self.vector_store.search(query_emb, top_k)

        chunks = session.query(Chunk).filter(Chunk.id.in_(ids.tolist())).all()

        session.close()
        return [c.text for c in chunks]


logging.getLogger("PyPDF2._cmap").setLevel(logging.ERROR)


def looks_sensitive(text: str) -> bool:
    lower = text.lower()
    for pattern in config.SECRET_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False


def load_documents(paths: List[Path] = None) -> List[str]:
    if paths is None:
        paths = config.RAG_PATHS

    all_texts = []

    for base_path in paths:
        if not base_path.exists():
            continue

        for root, dirs, files in os.walk(base_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in config.EXCLUDED_DIRS and not d.startswith(".")
            ]

            for filename in files:
                if filename.startswith("."):
                    continue

                file = Path(root) / filename

                try:
                    # Skip very large files
                    size_mb = file.stat().st_size / (1024 * 1024)
                    if size_mb > config.MAX_FILE_SIZE_MB:
                        continue
                except Exception:
                    continue

                try:
                    text = ""

                    # Try PDF first
                    if file.suffix.lower() == ".pdf":
                        reader = PdfReader(file)
                        text = "\n".join(
                            page.extract_text() or "" for page in reader.pages
                        )
                    else:
                        # Try reading as UTF-8 text
                        text = file.read_text(encoding="utf-8", errors="ignore")

                    if not text or not text.strip():
                        continue

                    # Basic binary detection, skip if too many null bytes
                    if "\x00" in text:
                        continue

                    # Secret detection AFTER reading
                    if looks_sensitive(text):
                        continue

                    all_texts.append(text)

                except Exception:
                    continue

    return all_texts


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap

    return chunks


def build_rag_index(batch_size: int = 5000) -> LocalRAG:
    from pathlib import Path
    import backend.config as config

    # Elimina índice viejo si existe
    Path(config.RAG_INDEX_PATH).unlink(missing_ok=True)
    Path(config.RAG_INDEX_PATH + ".docs").unlink(missing_ok=True)

    rag = LocalRAG()
    raw_docs = load_documents()

    # Fragmenta los documentos en chunks
    all_chunks = []
    for doc in raw_docs:
        all_chunks.extend(chunk_text(doc))

    if not all_chunks:
        raise ValueError("No se encontraron documentos para indexar")

    embedder = get_embedding_service()
    embeddings_list = []

    print(
        f"[BUILD] Total de chunks: {len(all_chunks)}. Procesando en batches de {batch_size}..."
    )

    # Procesa embeddings por lotes
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        batch_emb = embedder.embed_texts(batch)
        embeddings_list.append(batch_emb)

    # Une todos los embeddings y normaliza
    embeddings = np.vstack(embeddings_list).astype("float32")
    faiss.normalize_L2(embeddings)

    dims = embeddings.shape[1]
    print(
        f"[BUILD] Dimensiones de embeddings: {dims}, vectores totales: {embeddings.shape[0]}"
    )

    # Crea índice FAISS
    rag.index = faiss.IndexFlatL2(dims)
    rag.index.add(embeddings)
    rag.documents = all_chunks

    # Guarda índice y textos
    rag.save_index(config.RAG_INDEX_PATH)
    print(f"[SAVE] Índice guardado en {config.RAG_INDEX_PATH}")

    return rag
