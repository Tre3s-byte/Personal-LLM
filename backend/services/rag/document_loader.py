"""Document scanning and deterministic chunking for RAG indexing."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PyPDF2 import PdfReader

import backend.config as config


@dataclass(frozen=True)
class DocumentPayload:
    path: str
    stable_id: str
    checksum: str
    mtime: str
    text: str


def _stable_id(path: Path) -> str:
    return hashlib.sha1(str(path).encode("utf-8")).hexdigest()


def _checksum(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def looks_sensitive(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in config.SECRET_PATTERNS)


def _read_text(file_path: Path) -> str:
    if file_path.suffix.lower() == ".pdf":
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return file_path.read_text(encoding="utf-8", errors="ignore")


def load_documents(paths: list[Path] | None = None) -> list[DocumentPayload]:
    payloads: list[DocumentPayload] = []
    for base_path in paths or config.RAG_PATHS:
        if not base_path.exists():
            continue
        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if d not in config.EXCLUDED_DIRS and not d.startswith(".")]
            for filename in files:
                if filename.startswith("."):
                    continue
                file_path = Path(root) / filename
                try:
                    if file_path.stat().st_size > config.MAX_FILE_SIZE_MB * 1024 * 1024:
                        continue
                    text = _read_text(file_path)
                except Exception:
                    continue
                if not text.strip() or "\x00" in text or looks_sensitive(text):
                    continue
                payloads.append(
                    DocumentPayload(
                        path=str(file_path),
                        stable_id=_stable_id(file_path),
                        checksum=_checksum(file_path),
                        mtime=str(file_path.stat().st_mtime),
                        text=text,
                    )
                )
    return payloads


def chunk_text(text: str, chunk_size: int = config.RAG_CHUNK_SIZE, overlap: int = config.RAG_CHUNK_OVERLAP) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def iter_chunk_records(doc: DocumentPayload) -> Iterable[tuple[int, str]]:
    for idx, chunk in enumerate(chunk_text(doc.text)):
        yield idx, chunk
