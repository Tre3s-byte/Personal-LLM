"""Request router with deterministic shortcuts and semantic light-model routing."""

from backend.services.chunker.base import estimate_tokens
from backend.services.chat_manager import extract_last_user_message
from backend.utils.logging import app_logger

from .deterministic import extract_target_folder, route_deterministic
from .semantic import classify_with_small_model
from .strategy import select_strategy
from .patterns import MODEL_DIRECTIVE_PATTERN


def route_request(messages):
    text = extract_last_user_message(messages)
    token_estimate = estimate_tokens(text)

    deterministic_route = route_deterministic(text)
    if deterministic_route:
        app_logger.info(
            "Routing decision (deterministic)",
            extra={
                "extra_data": {
                    "event": "routing_decision",
                    "routing_source": "deterministic",
                    "route": deterministic_route,
                    "token_estimate": token_estimate,
                }
            },
        )
        return deterministic_route

    directive_match = MODEL_DIRECTIVE_PATTERN.search(text)
    model_override = directive_match.group("size").lower() if directive_match else None

    classification = classify_with_small_model(text)
    intent = str(classification["intent"])
    confidence = float(classification["confidence"])
    requires_rag = bool(classification.get("requires_rag", False))

    strategy = select_strategy(
        intent=intent,
        confidence=confidence,
        token_estimate=token_estimate,
        text=text,
        requires_rag=requires_rag,
        model_override=model_override,
    )
    strategy["router_source"] = classification.get("router_source", "unknown")

    app_logger.info(
        "Routing decision (semantic)",
        extra={
            "extra_data": {
                "event": "routing_decision",
                "routing_source": strategy["router_source"],
                "intent": intent,
                "confidence": confidence,
                "requires_rag": requires_rag,
                "model_override": model_override,
                "token_estimate": token_estimate,
                "rag_signals": classification.get("rag_signals", {}),
                "route": strategy,
            }
        },
    )

    return strategy


__all__ = ["route_request", "extract_target_folder"]
