"""Routing strategy selection from semantic intent and token budget."""

from typing import Any, Dict
from backend.config import ROUTER_HEAVY_THRESHOLD, ROUTER_LIGHT_THRESHOLD


def select_strategy(
    intent: str, confidence: float, token_estimate: int
) -> Dict[str, Any]:
    if confidence < 0.6:
        return {
            "task_type": "general_chat",
            "target_model": "medium",
            "chunk_strategy": None,
            "is_recommended": False,
            "intent": intent,
            "confidence": confidence,
        }

    if intent == "rag":
        return {
            "task_type": "rag_query",
            "target_model": "medium",
            "chunk_strategy": None,
            "requires_rag": True,
            "is_recommended": confidence > 0.85,
            "intent": intent,
            "confidence": confidence,
        }

    if intent == "code":
        is_heavy = token_estimate >= ROUTER_HEAVY_THRESHOLD
        return {
            "task_type": "code_heavy_review" if is_heavy else "code_review",
            "target_model": "large",
            "chunk_strategy": "code" if is_heavy else None,
            "is_recommended": confidence > 0.85,
            "intent": intent,
            "confidence": confidence,
        }

    if intent == "grammar":
        return {
            "task_type": "grammar",
            "target_model": "small",
            "chunk_strategy": None,
            "is_recommended": confidence > 0.85,
            "intent": intent,
            "confidence": confidence,
        }

    if intent == "log":
        is_long = token_estimate >= ROUTER_LIGHT_THRESHOLD
        return {
            "task_type": "log_summary" if is_long else "log_review",
            "target_model": "large"
            if token_estimate >= ROUTER_HEAVY_THRESHOLD
            else "medium",
            "chunk_strategy": "log" if is_long else None,
            "is_recommended": confidence > 0.85,
            "intent": intent,
            "confidence": confidence,
        }

    if intent == "summary":
        is_heavy = token_estimate >= ROUTER_HEAVY_THRESHOLD
        return {
            "task_type": "heavy_summary" if is_heavy else "light_summary",
            "target_model": "large" if is_heavy else "medium",
            "chunk_strategy": "log" if is_heavy else None,
            "is_recommended": confidence > 0.85,
            "intent": intent,
            "confidence": confidence,
        }

    if intent == "recommendation":
        is_long = token_estimate >= ROUTER_LIGHT_THRESHOLD
        return {
            "task_type": "recommend_long" if is_long else "recommend_short",
            "target_model": "medium" if is_long else "small",
            "chunk_strategy": "chat" if is_long else None,
            "is_recommended": confidence > 0.85,
            "intent": intent,
            "confidence": confidence,
        }

    is_short = token_estimate < ROUTER_LIGHT_THRESHOLD
    use_small = is_short and confidence > 0.85
    return {
        "task_type": "general_chat" if is_short else "general_long",
        "target_model": "small" if use_small else "medium",
        "chunk_strategy": None if is_short else "chat",
        "is_recommended": confidence > 0.85,
        "intent": intent,
        "confidence": confidence,
    }
