# backend/services/inference/chunker/code.py
import ast
from typing import List, Tuple
from .base import estimate_tokens, _split_large_block


def _extract_python_top_level_nodes(text: str) -> List[Tuple[int, int]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    spans: List[Tuple[int, int]] = []
    for node in tree.body:
        if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
            spans.append((node.lineno, node.end_lineno))
    return spans


def chunk_code(text: str, max_tokens: int) -> List[str]:
    lines = text.splitlines()
    if not lines:
        return []

    spans = _extract_python_top_level_nodes(text)
    if not spans:
        segments = [seg for seg in text.split("\n\n") if seg.strip()]
    else:
        segments = ["\n".join(lines[start - 1 : end]) for start, end in spans]

    chunks: List[str] = []
    current_segments: List[str] = []
    current_tokens = 0

    for segment in segments:
        seg_tokens = estimate_tokens(segment)
        if seg_tokens > max_tokens:
            if current_segments:
                chunks.append("\n\n".join(current_segments))
                current_segments = []
                current_tokens = 0
            chunks.extend(_split_large_block(segment.splitlines(), max_tokens))
            continue

        if current_segments and current_tokens + seg_tokens > max_tokens:
            chunks.append("\n\n".join(current_segments))
            current_segments = [segment]
            current_tokens = seg_tokens
        else:
            current_segments.append(segment)
            current_tokens += seg_tokens

    if current_segments:
        chunks.append("\n\n".join(current_segments))

    return chunks
