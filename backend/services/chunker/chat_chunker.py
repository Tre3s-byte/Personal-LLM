# backend/services/inference/chunker/chat.py
from typing import List, Dict
from .base import estimate_tokens


def _message_tokens(message: Dict[str, str]) -> int:
    role = message.get("role", "")
    content = message.get("content", "")
    return estimate_tokens(role) + estimate_tokens(content) + 4


def trim_chat_history(
    messages: List[Dict[str, str]], max_tokens: int
) -> List[Dict[str, str]]:
    """Keep system prompts + newest turns under token budget."""
    if not messages:
        return []

    system_messages = [m for m in messages if m.get("role") == "system"]
    other_messages = [m for m in messages if m.get("role") != "system"]

    selected: List[Dict[str, str]] = []
    current_tokens = sum(_message_tokens(m) for m in system_messages)

    for msg in reversed(other_messages):
        msg_tokens = _message_tokens(msg)
        if current_tokens + msg_tokens > max_tokens:
            break
        selected.append(msg)
        current_tokens += msg_tokens

    selected.reverse()
    return system_messages + selected
