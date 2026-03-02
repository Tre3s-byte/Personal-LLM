"""Heuristic request router mapping prompts to model/strategy selections."""

import re
from backend.config import ROUTER_LIGHT_THRESHOLD, ROUTER_HEAVY_THRESHOLD
from backend.services.chunker import estimate_tokens
from .chat_manager import extract_last_user_message

# ---- Precompiled patterns ----


RECOMMEND_PATTERN = re.compile(
    r"\b(recommend|recommendation|suggest|looking for|any good|similar to|based on)\b",
    re.IGNORECASE,
)

CODE_BLOCK_PATTERN = re.compile(
    r"```|def\s+\w+|class\s+\w+|#include|import\s+\w+|public\s+class"
)

CODE_INTENT_PATTERN = re.compile(
    r"\b(error|bug|fix|debug|traceback|exception|stacktrace|not working|doesn't work|issue|review this code|check this code|what's wrong|why is this failing|implement|how can i implement|refactor|optimize|performance|coding|programming|code review|syntax|logic|algorithm|function|variable|class|method|loop|condition|debugging|troubleshoot|resolve|improve code|efficiency|best practice|code quality|unit test|integration test)\b",
    re.IGNORECASE,
)

GRAMMAR_PATTERN = re.compile(
    r"\b(check grammar|fix grammar|correct this|rewrite this|improve wording|rephrase|make this clearer|spell check|proofread|edit|revise|polish|clarity|language|style|tone|concise|formal|informal|academic|professional)\b",
    re.IGNORECASE,
)

SUMMARY_PATTERN = re.compile(
    r"\b(summarize|summary|tldr|short version|condense|briefly explain|overview|key points|main ideas|recap|synopsis|abstract|highlight|essence|gist|bottom line|in short|to sum up)\b",
    re.IGNORECASE,
)

LOG_PATTERN = re.compile(
    r"\b(log|logs|stack trace|trace log|server output|console output|error log|access log)\b",
    re.IGNORECASE,
)

RAG_PATTERN = re.compile(
    r"\b(document|file|knowledge base|according to|based on the docs)\b",
    re.IGNORECASE,
)


def has_code_symbols(text: str) -> bool:
    if len(text) < 200:
        return False

    symbol_count = sum(1 for ch in text if ch in "{}();")
    return (symbol_count / len(text)) > 0.02


def route_request(messages):
    text = extract_last_user_message(messages)
    token_estimate = estimate_tokens(text)

    is_code_structure = CODE_BLOCK_PATTERN.search(text) is not None
    is_code_intent = CODE_INTENT_PATTERN.search(text) is not None
    is_grammar = GRAMMAR_PATTERN.search(text) is not None
    is_summary = SUMMARY_PATTERN.search(text) is not None
    is_recommend = RECOMMEND_PATTERN.search(text) is not None
    is_log = LOG_PATTERN.search(text) is not None

    if not is_code_structure and has_code_symbols(text):
        is_code_structure = True

    intention_count = (
        int(is_code_structure or is_code_intent)
        + int(is_grammar)
        + int(is_summary)
        + int(is_recommend)
        + int(is_log)
    )
    is_recommended = intention_count == 1

    if RAG_PATTERN.search(text):
        return {
            "task_type": "rag_query",
            "target_model": "medium",
            "chunk_strategy": None,
            "requires_rag": True,
        }

    if is_code_structure or is_code_intent:
        return {
            "task_type": "code_review"
            if token_estimate < ROUTER_HEAVY_THRESHOLD
            else "code_heavy_review",
            "target_model": "large",
            "chunk_strategy": "code"
            if token_estimate >= ROUTER_HEAVY_THRESHOLD
            else None,
            "is_recommended": is_recommended,
        }

    if is_grammar:
        return {
            "task_type": "grammar",
            "target_model": "small",
            "chunk_strategy": None,
            "is_recommended": is_recommended,
        }

    if is_log:
        return {
            "task_type": "log_summary"
            if token_estimate >= ROUTER_LIGHT_THRESHOLD
            else "log_review",
            "target_model": "medium"
            if token_estimate < ROUTER_HEAVY_THRESHOLD
            else "large",
            "chunk_strategy": "log"
            if token_estimate >= ROUTER_LIGHT_THRESHOLD
            else None,
            "is_recommended": is_recommended,
        }

    if is_summary:
        if token_estimate < ROUTER_HEAVY_THRESHOLD:
            return {
                "task_type": "light_summary",
                "target_model": "medium",
                "chunk_strategy": None,
                "is_recommended": is_recommended,
            }
        return {
            "task_type": "heavy_summary",
            "target_model": "large",
            "chunk_strategy": "log",
            "is_recommended": is_recommended,
        }

    if is_recommend:
        if token_estimate < ROUTER_LIGHT_THRESHOLD:
            return {
                "task_type": "recommend_short",
                "target_model": "small",
                "chunk_strategy": None,
                "is_recommended": is_recommended,
            }
        return {
            "task_type": "recommend_long",
            "target_model": "medium",
            "chunk_strategy": "chat",
            "is_recommended": is_recommended,
        }

    if token_estimate < ROUTER_LIGHT_THRESHOLD:
        return {
            "task_type": "general_chat",
            "target_model": "small",
            "chunk_strategy": None,
            "is_recommended": is_recommended,
        }

    return {
        "task_type": "general_long",
        "target_model": "medium",
        "chunk_strategy": "chat",
        "is_recommended": is_recommended,
    }
