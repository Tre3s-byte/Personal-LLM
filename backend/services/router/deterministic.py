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

INVALID_FOLDER_WORDS = {"download", "save", "store", "put", "move"}


def extract_target_folder(text: str) -> Optional[str]:
    """
    Extract folder if explicitly mentioned (after 'in', 'into', 'to', etc.).
    Returns None if no valid folder is found or matched word is invalid.
    """
    sanitized = YOUTUBE_URL_PATTERN.sub("", text)
    match = FOLDER_PATTERN.search(sanitized)

    if not match:
        app_logger.info("No explicit folder found in text")
        return None

    try:
        folder = match.group("folder").strip()
        folder = re.split(
            r"\b(please|thanks|now|this|that|and|for|the)\b",
            folder,
            flags=re.IGNORECASE,
        )[0].strip()

        # Ignore invalid folder names (verbs or generic actions)
        if not folder or folder.lower() in INVALID_FOLDER_WORDS:
            app_logger.info(f"Ignored invalid folder name: {folder}")
            return None

        folder_name = folder.title()
        app_logger.info(f"Extracted explicit folder name: {folder_name}")
        return folder_name

    except Exception as e:
        app_logger.exception(f"Error extracting folder name: {e}")
        return None


def route_deterministic(text: str) -> Optional[Dict[str, Any]]:
    has_url = YOUTUBE_URL_PATTERN.search(text)
    has_action = YOUTUBE_ACTION_PATTERN.search(text) or YOUTUBE_ADD_PATTERN.search(text)
    is_hypothetical = YOUTUBE_HYPOTHETICAL_PATTERN.search(text)
    directive_match = MODEL_DIRECTIVE_PATTERN.search(text)

    if directive_match:
        target_model = directive_match.group("size").lower()
    else:
        target_model = "small"
        app_logger.info("No model directive found; using default 'small'")

    if has_url and has_action and not is_hypothetical:
        folder_name = extract_target_folder(text)  # can be None
        app_logger.info(
            "Deterministic route matched youtube backup",
            extra={
                "extra_data": {
                    "event": "route_deterministic_match",
                    "task_type": "youtube_backup",
                    "target_model": target_model,
                    "target_folder": folder_name or "(will use RAG/model to decide)",
                }
            },
        )
        return {
            "task_type": "youtube_backup",
            "target_model": target_model,
            "target_folder": folder_name,  # None if not explicit
            "chunk_strategy": None,
            "requires_rag": folder_name is None,  # use RAG if folder unknown
            "is_recommended": True,
        }

    return None
