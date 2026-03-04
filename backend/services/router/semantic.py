"""Semantic router using lightweight model + deterministic RAG relevance signals."""

import json
import math
import re
from typing import Any, Dict

from backend.services.inference.llama import _generate_with_model
from backend.services.router import patterns
from backend.utils.logging import app_logger


FILE_TYPE_PATTERN = re.compile(r"\.(pdf|csv|mp3|txt|md|docx?|xlsx?|json|yaml|yml|log)\b", re.IGNORECASE)
FILE_PATH_PATTERN = re.compile(r"([a-zA-Z]:\\[^\s]+|/[^\s]+|\.{1,2}/[^\s]+)")
FILENAME_PATTERN = re.compile(r"\b[\w\- ]+\.[a-zA-Z0-9]{2,6}\b")
URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
PRONOUN_PATTERN = re.compile(r"\b(this|that|it|these|those)\b", re.IGNORECASE)
RAG_KEYWORD_PATTERN = re.compile(
    r"\b(info|data|remember|summary|notes|project|indexed|index|scraped|document|knowledge|context)\b",
    re.IGNORECASE,
)
KNOWLEDGE_QUERY_PATTERN = re.compile(
    r"\b(what|where|which|who|when|how|tell me|do we have|can you find|search|lookup)\b",
    re.IGNORECASE,
)
FILE_MANAGEMENT_PATTERN = re.compile(
    r"\b(put|store|save|move|organize|folder|directory|path|location|where should i put)\b",
    re.IGNORECASE,
)
SUMMARY_PATTERN = re.compile(r"\b(summarize|summary|recap|condense|tl;dr)\b", re.IGNORECASE)

VALID_INTENTS = {
    "youtube_backup",
    "file_management",
    "knowledge_query",
    "summary",
    "grammar",
    "general_chat",
}


def softmax(scores: dict[str, float]) -> dict[str, float]:
    exp_scores = {k: math.exp(v) for k, v in scores.items()}
    total = sum(exp_scores.values())
    return {k: v / total for k, v in exp_scores.items()}


def _detect_rag_signals(text: str) -> dict[str, bool]:
    return {
        "has_url": bool(URL_PATTERN.search(text)),
        "has_file_path": bool(FILE_PATH_PATTERN.search(text)),
        "has_filename": bool(FILENAME_PATTERN.search(text)),
        "has_file_type": bool(FILE_TYPE_PATTERN.search(text)),
        "has_ambiguous_pronoun": bool(PRONOUN_PATTERN.search(text)),
        "has_rag_keyword": bool(RAG_KEYWORD_PATTERN.search(text)),
        "mentions_indexed_or_scraped": bool(
            re.search(r"\b(indexed|ingested|scraped|from my docs|from my files)\b", text, re.IGNORECASE)
        ),
    }


def classify_intent(text: str) -> Dict[str, Any]:
    """Heuristic intent + requires_rag classification used as safe fallback."""

    rag_signals = _detect_rag_signals(text)
    requires_rag = any(rag_signals.values())

    scores = {
        "youtube_backup": 0.0,
        "file_management": 0.0,
        "knowledge_query": 0.0,
        "summary": 0.0,
        "grammar": 0.0,
        "general_chat": 0.2,
    }

    if patterns.YOUTUBE_URL_PATTERN.search(text):
        scores["youtube_backup"] += 0.8
    if patterns.YOUTUBE_ACTION_PATTERN.search(text) or patterns.YOUTUBE_ADD_PATTERN.search(text):
        scores["youtube_backup"] += 0.7

    if FILE_MANAGEMENT_PATTERN.search(text):
        scores["file_management"] += 0.7
    if SUMMARY_PATTERN.search(text):
        scores["summary"] += 0.85
    if patterns.GRAMMAR_PATTERN.search(text):
        scores["grammar"] += 0.9
    if KNOWLEDGE_QUERY_PATTERN.search(text) or rag_signals["has_rag_keyword"]:
        scores["knowledge_query"] += 0.65

    if requires_rag:
        scores["knowledge_query"] += 0.25
        scores["file_management"] += 0.15

    dominant_intent = max(scores, key=scores.get)
    probs = softmax(scores)
    confidence = round(float(probs[dominant_intent]), 2)

    # Prefer RAG-relevant categories when ties/near-ties happen.
    if requires_rag and dominant_intent == "general_chat":
        dominant_intent = "knowledge_query"
        confidence = max(confidence, 0.7)

    return {
        "intent": dominant_intent,
        "confidence": confidence,
        "requires_rag": requires_rag,
        "router_source": "heuristic",
        "rag_signals": rag_signals,
    }


def _build_router_prompt(text: str, heuristic: Dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a lightweight semantic router. Return ONLY JSON with keys: "
                "intent, requires_rag, confidence. "
                "Allowed intents: youtube_backup, file_management, knowledge_query, summary, grammar, general_chat. "
                "If the user references URLs/files/previously indexed content or ambiguous content pronouns, requires_rag should be true."
            ),
        },
        {
            "role": "user",
            "content": (
                f"User prompt:\n{text}\n\n"
                f"Heuristic hint (JSON): {json.dumps({'intent': heuristic['intent'], 'requires_rag': heuristic['requires_rag'], 'rag_signals': heuristic['rag_signals']})}"
            ),
        },
    ]


def classify_with_small_model(text: str) -> Dict[str, Any]:
    """Use small model for routing; fall back to deterministic heuristics safely."""

    fallback = classify_intent(text)

    try:
        output = _generate_with_model("small", _build_router_prompt(text, fallback), max_tokens=120)
        raw_text = (output.get("text") or "").strip().strip("`")
        parsed = json.loads(raw_text)

        intent = str(parsed.get("intent", fallback["intent"]))
        requires_rag = bool(parsed.get("requires_rag", fallback["requires_rag"]))
        confidence = round(float(parsed.get("confidence", fallback["confidence"])), 2)

        if intent not in VALID_INTENTS:
            raise ValueError(f"invalid intent from small model router: {intent}")

        decision = {
            "intent": intent,
            "requires_rag": requires_rag,
            "confidence": min(max(confidence, 0.0), 1.0),
            "router_source": "small_model",
            "rag_signals": fallback["rag_signals"],
        }
        app_logger.info(
            "Semantic router decision",
            extra={"extra_data": {"event": "semantic_router_decision", "decision": decision}},
        )
        return decision
    except Exception as exc:
        app_logger.warning(f"Small-model routing failed; using heuristic router: {exc}")
        return fallback
