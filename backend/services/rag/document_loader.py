import re
import os
import logging
from pathlib import Path
from PyPDF2 import PdfReader
from typing import List
import backend.config as config

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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
        logger.info(f"Scanning {base_path}")
        if not base_path.exists():
            logger.warning(f"Path does not exist: {base_path}")
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
                logger.info(f"Checking file: {file}")

                try:
                    size_mb = file.stat().st_size / (1024 * 1024)
                    if size_mb > config.MAX_FILE_SIZE_MB:
                        logger.info(
                            f"Skipping large file (> {config.MAX_FILE_SIZE_MB}MB): {file}"
                        )
                        continue
                except Exception as e:
                    logger.warning(f"Failed to get file size for {file}: {e}")
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
                        logger.info(f"Skipping empty or binary file: {file}")
                        continue
                    if looks_sensitive(text):
                        logger.info(f"Skipping sensitive file: {file}")
                        continue

                    all_texts.append(text)
                    logger.info(f"Loaded text from: {file} ({len(text)} chars)")
                except Exception as e:
                    logger.error(f"Error reading {file}: {e}")
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
