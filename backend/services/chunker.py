import ast
import re
from typing import Dict, List, Tuple


def estimate_tokens(text: str) -> int:
    return max(1, len(text) >> 2)


def _message_tokens(message: Dict[str, str]) -> int:
    role = message.get("role", "")
    content = message.get("content", "")
    return estimate_tokens(role) + estimate_tokens(content) + 4


def trim_chat_history(messages: List[Dict[str, str]], max_tokens: int) -> List[Dict[str, str]]:
    """Keep system prompts and newest conversational turns under a token budget."""
    if not messages:
        return []

    system_messages = [msg for msg in messages if msg.get("role") == "system"]
    other_messages = [msg for msg in messages if msg.get("role") != "system"]

    selected: List[Dict[str, str]] = []
    current_tokens = sum(_message_tokens(msg) for msg in system_messages)

    for msg in reversed(other_messages):
        msg_tokens = _message_tokens(msg)
        if current_tokens + msg_tokens > max_tokens:
            break
        selected.append(msg)
        current_tokens += msg_tokens

    selected.reverse()
    return system_messages + selected


def _split_log_blocks(text: str) -> List[str]:
    lines = text.splitlines()
    if not lines:
        return []

    ts_pattern = re.compile(r"^\s*(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}|\[\d{2}:\d{2}:\d{2}\]|\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})")

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


def _split_large_block(lines: List[str], max_tokens: int) -> List[str]:
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


def chunk_code(text: str, max_tokens: int) -> List[str]:
    """Chunk code by top-level syntax boundaries, then by logical line blocks if needed."""
    lines = text.splitlines()
    if not lines:
        return []

    spans = _extract_python_top_level_nodes(text)

    if not spans:
        # Fallback to paragraph/blank-line segmentation for non-python code.
        segments = [segment for segment in text.split("\n\n") if segment.strip()]
    else:
        segments = ["\n".join(lines[start - 1:end]) for start, end in spans]

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
