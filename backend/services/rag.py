"""Retrieval-Augmented Generation primitives and document ingestion pipeline."""

import os
import faiss
import numpy as np
from pathlib import Path
from typing import List
from PyPDF2 import PdfReader
import config
import logging
import re

from .embeddings import get_embedding_service


class LocalRAG:
    def __init__(self):
        self.embedder = None
        self.index = None
        self.documents: List[str] = []

    def _get_embedder(self):
        if self.embedder is None:
            self.embedder = get_embedding_service()
        return self.embedder

    def build_index(self, texts: List[str]):
        if not texts:
            raise ValueError("No documents provided to build index")

        embedder = self._get_embedder()
        embeddings = embedder.embed_texts(texts)
        embeddings = np.array(embeddings, dtype="float32")
        faiss.normalize_L2(embeddings)

        dimensions = embeddings.shape[-1]
        self.index = faiss.IndexFlatL2(dimensions)
        self.index.add(embeddings)

        self.documents = texts
        self.save_index(config.RAG_INDEX_PATH)

    def save_index(self, path: str):
        if self.index is None:
            return
        index_dir = Path(path).parent
        index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, path)
        doc_path = path + ".docs"
        with open(doc_path, "w", encoding="utf-8") as f:
            for doc in self.documents:
                f.write(doc.replace("\n", " " + "\n"))

    def load_index(self, path: str):
        if not Path(path).exists():
            return False
        self.index = faiss.read_index(path)

        doc_path = path + ".docs"
        self.documents = []
        if Path(doc_path).exists():
            with open(doc_path, "r", encoding="utf-8") as f:
                self.documents = [line.strip() for line in f if line.strip()]
        return True

    def search(self, query: str, top_k: int = 4) -> List[str]:
        if self.index is None:
            raise RuntimeError("Index not loaded")
        embedder = self._get_embedder()

        query_vec = embedder.embed_texts(query)

        if not isinstance(query_vec, np.ndarray):
            query_vec = np.array(query_vec)

        query_vec = query_vec.astype("float32").reshape(1, -1)

        faiss.normalize_L2(query_vec)

        distances, indices = self.index.search(query_vec, top_k)

        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.documents):
                results.append(self.documents[idx])

        return results


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


def build_rag_index() -> LocalRAG:
    rag = LocalRAG()

    raw_docs = load_documents()

    all_chunks = []
    for doc in raw_docs:
        chunks = chunk_text(doc)
        all_chunks.extend(chunks)

    rag.build_index(all_chunks)

    return rag
