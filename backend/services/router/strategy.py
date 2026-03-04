"""Routing strategy selection from semantic intent and token budget."""

from typing import Any, Dict
from backend.config import ROUTER_HEAVY_THRESHOLD, ROUTER_LIGHT_THRESHOLD


def infer_chunk_strategy(text: str, token_estimate: int, intent: str) -> str | None:
    lowered = text.lower()
    if "```" in text or any(
        marker in lowered for marker in ["def ", "class ", "#include", "import "]
    ):
        return "code"
    if any(
        marker in lowered
        for marker in ["error", "exception", "traceback", "stack trace", "log:"]
    ):
        return "log"
    if token_estimate >= ROUTER_LIGHT_THRESHOLD:
        return "chat"
    if intent == "summary" and token_estimate >= 300:
        return "log"
    return None


def select_strategy(
    *,
    intent: str,
    confidence: float,
    token_estimate: int,
    text: str,
    requires_rag: bool,
    model_override: str | None = None,
) -> Dict[str, Any]:
    chunk_strategy = infer_chunk_strategy(
        text=text, token_estimate=token_estimate, intent=intent
    )

    if intent == "youtube_backup":
        task_type = "youtube_backup"
        default_model = "small"
    elif intent == "file_management":
        task_type = "file_management"
        default_model = "small" if requires_rag else "medium"
    elif intent == "knowledge_query":
        task_type = "knowledge_query"
        default_model = "small" if requires_rag else "medium"
    elif intent == "summary":
        task_type = "summary"
        default_model = "small" if requires_rag else "medium"
        if chunk_strategy is None and token_estimate >= 300:
            chunk_strategy = "log"
    elif intent == "grammar":
        task_type = "grammar"
        default_model = "small"
        chunk_strategy = None
    else:
        task_type = "general_chat"
        default_model = "medium" if not requires_rag else "small"

    if chunk_strategy in {"code", "log"} and token_estimate >= ROUTER_HEAVY_THRESHOLD:
        default_model = "large"

    target_model = model_override or default_model

    if not requires_rag and model_override is None and intent == "general_chat":
        target_model = "medium"

    return {
        "task_type": task_type,
        "target_model": target_model,
        "chunk_strategy": chunk_strategy,
        "requires_rag": requires_rag,
        "is_recommended": confidence > 0.85,
        "intent": intent,
        "confidence": confidence,
    }
