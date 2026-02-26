import re
from config import ROUTER_LIGHT_THRESHOLD, ROUTER_HEAVY_THRESHOLD

# ---- Precompiled patterns ----

RECOMMEND_PATTERN = re.compile(
    r"\b(recommend|recommendation|suggest|looking for|any good|similar to|based on)\b",
    re.IGNORECASE
)

CODE_BLOCK_PATTERN = re.compile(
    r"```|def\s+\w+|class\s+\w+|#include|import\s+\w+|public\s+class"
)

CODE_INTENT_PATTERN = re.compile(
    r"\b(error|bug|fix|debug|traceback|exception|stacktrace|not working|doesn't work|issue|review this code|check this code|what's wrong|why is this failing|implement|how can i implement|refactor|optimize|performance|coding|programming|code review|syntax|logic|algorithm|function|variable|class|method|loop|condition|debugging|troubleshoot|resolve|improve code|efficiency|best practice|code quality|unit test|integration test)\b",
    re.IGNORECASE
)

GRAMMAR_PATTERN = re.compile(
    r"\b(check grammar|fix grammar|correct this|rewrite this|improve wording|rephrase|make this clearer|spell check|proofread|edit|revise|polish|clarity|language|style|tone|concise|formal|informal|academic|professional)\b",
    re.IGNORECASE
)

SUMMARY_PATTERN = re.compile(
    r"\b(summarize|summary|tldr|short version|condense|briefly explain|overview|key points|main ideas|recap|synopsis|abstract|highlight|essence|gist|bottom line|in short|to sum up)\b",
    re.IGNORECASE
)




def extract_last_user_message(messages):
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def estimate_tokens(text: str) -> int:
    return len(text) >> 2


def has_code_symbols(text: str) -> bool:
    if len(text) < 200:
        return False

    symbol_count = 0
    for ch in text:
        if ch in "{}();":
            symbol_count += 1

    return (symbol_count / len(text)) > 0.02


def route_request(messages):
    text = extract_last_user_message(messages)
    token_estimate = estimate_tokens(text)

    # ---- Intent detection ----

    is_code_structure = CODE_BLOCK_PATTERN.search(text) is not None
    is_code_intent = CODE_INTENT_PATTERN.search(text) is not None
    is_grammar = GRAMMAR_PATTERN.search(text) is not None
    is_summary = SUMMARY_PATTERN.search(text) is not None
    is_recommend = RECOMMEND_PATTERN.search(text) is not None

    # Lightweight structural boost
    if not is_code_structure and has_code_symbols(text):
        is_code_structure = True

    # Intention confidence flag
    intention_count = (
        int(is_code_structure or is_code_intent)
        + int(is_grammar)
        + int(is_summary)
        + int(is_recommend)
    )
    is_recommended = intention_count == 1

    # ---- CODE ----
    if is_code_structure or is_code_intent:
        return {
            "task_type": "code_review" if token_estimate < ROUTER_HEAVY_THRESHOLD else "code_heavy_review",
            "target_model": "large",
            "needs_chunking": token_estimate >= ROUTER_HEAVY_THRESHOLD,
            "is_recommended": is_recommended
            }
    
    # ---- GRAMMAR ----
    if is_grammar:
        return {
            "task_type": "grammar",
            "target_model": "small",
            "needs_chunking": False,
            "is_recommended": is_recommended
        }

    # ---- SUMMARY ----
    if is_summary:
        if token_estimate < ROUTER_HEAVY_THRESHOLD:
            return {
                "task_type": "light_summary",
                "target_model": "medium",
                "needs_chunking": False,
                "is_recommended": is_recommended
            }
        return {
            "task_type": "heavy_summary",
            "target_model": "large",
            "needs_chunking": True,
            "is_recommended": is_recommended
        }

    # ---- RECOMMENDATION ----
    if is_recommend:
        if token_estimate < ROUTER_LIGHT_THRESHOLD:
            return {
                "task_type": "recommend_short",
                "target_model": "small",
                "needs_chunking": False,
                "is_recommended": is_recommended
            }
        return {
            "task_type": "recommend_long",
            "target_model": "medium",
            "needs_chunking": False,
            "is_recommended": is_recommended
        }

    # ---- DEFAULT ----
    if token_estimate < ROUTER_LIGHT_THRESHOLD:
        return {
            "task_type": "general_chat",
            "target_model": "small",
            "needs_chunking": False,
            "is_recommended": is_recommended
        }

    return {
        "task_type": "general_long",
        "target_model": "medium",
        "needs_chunking": False,
        "is_recommended": is_recommended
    }