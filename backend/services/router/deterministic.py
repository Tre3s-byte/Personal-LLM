import re
from typing import Any, Dict, Optional
from .patterns import (
    FOLDER_PATTERN,
    MODEL_DIRECTIVE_PATTERN,
    YOUTUBE_ADD_PATTERN,
    YOUTUBE_HYPOTHETICAL_PATTERN,
    YOUTUBE_URL_PATTERN,
    YOUTUBE_ACTION_PATTERN,
)
from backend.utils.logging import app_logger


def extract_target_folder(text: str) -> str:
    sanitized = YOUTUBE_URL_PATTERN.sub("", text)
    match = FOLDER_PATTERN.search(sanitized)

    if not match:
        app_logger.info("No folder pattern matched; defaulting to 'Liked Songs'")
        return "Liked Songs"

    try:
        folder = match.group("folder").strip()
        folder = re.split(
            r"\b(please|thanks|now|this|that|and|for)\b", folder, flags=re.IGNORECASE
        )[0].strip()

        folder_name = folder.title() if folder else "Liked Songs"
        app_logger.info(f"Extracted folder name: {folder_name}")
        return folder_name

    except Exception as e:
        app_logger.exception(f"Error extracting folder name: {e}")
        return "Liked Songs"


def route_deterministic(text: str) -> Optional[Dict[str, Any]]:
    has_url = YOUTUBE_URL_PATTERN.search(text)
    has_action = YOUTUBE_ACTION_PATTERN.search(text) or YOUTUBE_ADD_PATTERN.search(text)
    is_hypothetical = YOUTUBE_HYPOTHETICAL_PATTERN.search(text)
    directive_match = MODEL_DIRECTIVE_PATTERN.search(text)

    if directive_match:
        target_model = directive_match.group(1).lower()
    else:
        target_model = "small"  # default fallback
    if not directive_match:
        app_logger.info("No model directive found; using default 'medium'")
    if has_url and has_action and not is_hypothetical:
        return {
            "task_type": "general_chat",
            "target_model": target_model,  # safe fallback used here
            "chunk_strategy": None,
            "is_recommended": True,
        }
    return None
