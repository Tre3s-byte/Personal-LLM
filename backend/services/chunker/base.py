# backend/services/inference/chunker/base.py
from typing import List


def estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token ~ 4 characters."""
    return max(1, len(text) >> 2)


def _split_large_block(lines: List[str], max_tokens: int) -> List[str]:
    """Split a list of lines into chunks respecting max_tokens."""
    chunks: List[str] = []
    current: List[str] = []
    current_tokens = 0

    for line in lines:
        line_tokens = estimate_tokens(line)
        if current and current_tokens + line_tokens > max_tokens:
            chunks.append("\n".join(current))
            current = [line]
            current_tokens = line_tokens
        else:
            current.append(line)
            current_tokens += line_tokens

    if current:
        chunks.append("\n".join(current))

    return chunks
