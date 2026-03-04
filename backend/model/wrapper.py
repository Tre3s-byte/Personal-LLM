"""Inference orchestration wrapper with centralized structured logging."""

from __future__ import annotations

import time
import uuid

from backend.services.inference import run_routed_inference
from backend.services.router import route_request
from backend.utils.logging import (
    log_event,
    log_inference_request,
    log_inference_response,
    log_inference_telemetry,
    setup_logging,
)

app_logger, _, telemetry_logger = setup_logging()


def handle_request(messages: list[dict[str, str]]) -> str:
    request_id = str(uuid.uuid4())
    started = time.perf_counter()
    prompt = messages[-1].get("content", "") if messages else ""

    log_inference_request(
        request_id=request_id,
        prompt=prompt,
        model_name="auto",
        strategy="router",
    )
    log_event(app_logger, "incoming_request", request_id=request_id, user_context=messages)

    route_info = route_request(messages)
    selected_model = route_info.get("selected_model") or route_info.get("target_model")
    log_event(
        app_logger,
        "routing_completed",
        request_id=request_id,
        selected_model=selected_model,
        fallback_model=route_info.get("fallback_model"),
        chunk_strategy=route_info.get("chunk_strategy"),
        task_type=route_info.get("task_type"),
    )

    response = run_routed_inference(
        model_name=selected_model,
        messages=messages,
        routing=route_info,
    )

    latency = time.perf_counter() - started
    usage = response.get("usage", {}) if isinstance(response, dict) else {}
    response_text = response.get("text", "") if isinstance(response, dict) else str(response)

    log_inference_response(
        request_id=request_id,
        response_text=response_text,
        model_name=str(selected_model),
        inference_process_time=latency,
    )
    log_inference_telemetry(
        request_id=request_id,
        model_used=str(selected_model),
        task_type=route_info.get("task_type"),
        inference_process_time=latency,
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
        total_tokens=int(usage.get("total_tokens") or 0),
    )
    log_event(telemetry_logger, "request_complete", request_id=request_id, latency_seconds=latency)

    return response_text
