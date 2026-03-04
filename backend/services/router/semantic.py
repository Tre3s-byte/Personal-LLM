"""Semantic intent classification for non-deterministic requests."""

import math
from backend.services.router import patterns
from typing import Dict


def has_code_symbols(text: str) -> bool:
    if len(text) < 100:
        return False

    symbols = set("{}()[];:=<>#")
    symbol_count = sum(1 for ch in text if ch in symbols)

    density = symbol_count / len(text)
    return density > 0.015


def softmax(scores: dict[str, float]) -> dict[str, float]:
    exp_scores = {k: math.exp(v) for k, v in scores.items()}
    total = sum(exp_scores.values())
    return {k: v / total for k, v in exp_scores.items()}


def classify_intent(text: str) -> Dict[str, float | str]:
    """Return a structured dominant intent + confidence.

    This is intentionally lightweight and deterministic until a dedicated
    classifier model is plugged in.
    """

    intent_patterns = [
        (patterns.YOUTUBE_URL_PATTERN, "youtube_backup", 0.2),
        (patterns.RECOMMEND_PATTERN, "recommendation", 0.8),
        (patterns.SUMMARY_PATTERN, "summary", 0.8),
        (patterns.GRAMMAR_PATTERN, "grammar", 0.85),
        (patterns.LOG_PATTERN, "log", 0.8),
        (patterns.RAG_PATTERN, "rag", 0.8),
        (patterns.CODE_BLOCK_PATTERN, "code", 0.85),
        (patterns.CODE_INTENT_PATTERN, "code", 0.85),
    ]

    scores = {intent: 0.0 for intent in patterns.INTENTS}
    if has_code_symbols(text):
        scores["code"] += 0.2
    for pattern, intent, weight in intent_patterns:
        if pattern.search(text):
            scores[intent] += weight

    probs = softmax(scores)
    dominant_intent = max(probs, key=probs.get)
    top_score = scores[dominant_intent]
    confidence = probs[dominant_intent]

    if top_score <= 0.2:
        dominant_intent = "chat"
        confidence = 0.5

    return {
        "intent": dominant_intent,
        "confidence": round(float(confidence), 2),
    }
