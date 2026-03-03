# backend/services/inference/chunker/logs.py
import re
from typing import List
from .base import estimate_tokens, _split_large_block


def _split_log_blocks(text: str) -> List[str]:
    lines = text.splitlines()
    if not lines:
        return []

    ts_pattern = re.compile(
        r"^\s*(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}|\[\d{2}:\d{2}:\d{2}\]|\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
    )

    blocks: List[str] = []
    current: List[str] = []

    for line in lines:
        is_boundary = bool(ts_pattern.match(line))
        if is_boundary and current:
            blocks.append("\n".join(current))
            current = [line]
            continue
        if not line.strip() and current:
            blocks.append("\n".join(current))
            current = []
            continue
        current.append(line)

    if current:
        blocks.append("\n".join(current))

    return [b for b in blocks if b.strip()]


def chunk_log_text(text: str, max_tokens: int) -> List[str]:
    blocks = _split_log_blocks(text)
    if not blocks:
        return []

    chunks: List[str] = []
    current: List[str] = []
    current_tokens = 0

    for block in blocks:
        block_tokens = estimate_tokens(block)
        if current and current_tokens + block_tokens > max_tokens:
            chunks.append("\n\n".join(current))
            current = [block]
            current_tokens = block_tokens
        else:
            current.append(block)
            current_tokens += block_tokens

    if current:
        chunks.append("\n\n".join(current))

    return chunks
