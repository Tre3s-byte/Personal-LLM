"""Request router with staged deterministic + semantic classification."""

from backend.services.chunker.base import estimate_tokens
from backend.services.chat_manager import extract_last_user_message
from .deterministic import route_deterministic, extract_target_folder
from .semantic import classify_intent
from .strategy import select_strategy


def route_request(messages):
    text = extract_last_user_message(messages)
    token_estimate = estimate_tokens(text)

    deterministic_route = route_deterministic(text)
    if deterministic_route:
        return deterministic_route

    classification = classify_intent(text)
    intent = classification["intent"]
    confidence = classification["confidence"]

    return select_strategy(
        intent=intent, confidence=confidence, token_estimate=token_estimate
    )


__all__ = ["route_request", "extract_target_folder"]
