# backend/services/inference/misc.py
from typing import List, Dict

# Optional helpers, can be used by prompt_handler.py or llama.py


def _extract_latest_user_text(messages: List[Dict[str, str]]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def _aggregate_usage(aggregate: Dict[str, int], usage: Dict[str, int]):
    for key in aggregate:
        aggregate[key] += int(usage.get(key) or 0)
