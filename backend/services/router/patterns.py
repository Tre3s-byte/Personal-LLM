"""Regex patterns shared by routing stages."""

import re
from typing import List, Dict, Tuple, Pattern
import json
from pathlib import Path

DATA_BASE = Path(__file__).resolve().parent.parent.parent
KEYWORDS_PATH = DATA_BASE / "data" / "keywords.json"

with KEYWORDS_PATH.open("r", encoding="utf-8") as f:
    keyword_data = json.load(f)


# ------------------------
# Helper to compile regex
# ------------------------
def compile_keywords(keywords: List[str], word_boundaries: bool = True) -> Pattern:
    escaped = [re.escape(k) for k in keywords]
    pattern = "|".join(escaped)
    if word_boundaries:
        pattern = rf"\b({pattern})\b"
    else:
        pattern = rf"({pattern})"
    return re.compile(pattern, re.IGNORECASE)


def get_keywords(key: str) -> list:
    if key not in keyword_data:
        raise KeyError(f"Missing '{key}' in keywords.json")
    return keyword_data[key]


# ------------------------
# Compile patterns
# ------------------------
CODE_INTENT_PATTERN = compile_keywords(keyword_data["code_keywords"])
GRAMMAR_PATTERN = compile_keywords(keyword_data["grammar_keywords"])
YOUTUBE_ACTION_PATTERN = compile_keywords(keyword_data["youtube_keywords"])
RECOMMEND_PATTERN = compile_keywords(keyword_data["recommend_keywords"])
SUMMARY_PATTERN = compile_keywords(keyword_data["summary_keywords"])
LOG_PATTERN = compile_keywords(keyword_data["log_keywords"])
RAG_PATTERN = compile_keywords(keyword_data["rag_keywords"])


# Static regex patterns
FOLDER_PATTERN = re.compile(
    r"""
    \b
    (?:in|into|to|under|inside|store\ in|save\ in)
    \s+
    (?P<folder>[a-zA-Z0-9 _-]+)
    """,
    re.IGNORECASE | re.VERBOSE,
)

YOUTUBE_URL_PATTERN = re.compile(
    r"""
    (?:https?://)?
    (?:www\.)?
    (?:youtube\.com|youtu\.be)
    /
    \S+
    """,
    re.IGNORECASE | re.VERBOSE,
)

YOUTUBE_ADD_PATTERN = re.compile(r"\b(add|put)\s+this\s+to\b", re.IGNORECASE)

YOUTUBE_HYPOTHETICAL_PATTERN = re.compile(
    r"""
    \b
    (
        if\s+i\s+(?:were|was|could|can)\s+to\s+(?:download|save|backup)
        |
        how\s+to\s+(?:download|save|backup)
    )
    \b
    """,
    re.IGNORECASE | re.VERBOSE,
)

MODEL_DIRECTIVE_PATTERN = re.compile(
    r"\buse the (?P<size>small|medium|large) model\b",
    re.IGNORECASE,
)

CODE_BLOCK_PATTERN = re.compile(
    r"""
    ``` |
    def\s+\w+ |
    class\s+\w+ |
    \#include |
    import\s+\w+ |
    public\s+class
    """,
    re.VERBOSE,
)

# ------------------------
# Intents
# ------------------------
INTENTS = [
    "youtube_backup",
    "recommendation",
    "summary",
    "grammar",
    "code",
    "log",
    "rag",
    "chat",
]

INTENT_PATTERNS = {
    "youtube_backup": [(YOUTUBE_URL_PATTERN, 0.2), (YOUTUBE_ACTION_PATTERN, 0.2)],
    "recommendation": [(RECOMMEND_PATTERN, 0.8)],
    "summary": [(SUMMARY_PATTERN, 0.8)],
    "grammar": [(GRAMMAR_PATTERN, 0.85)],
    "log": [(LOG_PATTERN, 0.8)],
    "rag": [(RAG_PATTERN, 0.8)],
    "code": [(CODE_BLOCK_PATTERN, 0.85), (CODE_INTENT_PATTERN, 0.85)],
}
