import re
import os
from pathlib import Path
from PyPDF2 import PdfReader
from typing import List
import backend.config as config


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
                    size_mb = file.stat().st_size / (1024 * 1024)
                    if size_mb > config.MAX_FILE_SIZE_MB:
                        continue
                except Exception:
                    continue
                try:
                    text = ""
                    if file.suffix.lower() == ".pdf":
                        reader = PdfReader(file)
                        text = "\n".join(
                            page.extract_text() or "" for page in reader.pages
                        )
                    else:
                        text = file.read_text(encoding="utf-8", errors="ignore")
                    if not text.strip() or "\x00" in text:
                        continue
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
