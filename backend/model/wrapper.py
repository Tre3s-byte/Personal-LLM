import logging
import uuid
import time

from services.router import route_request
from services.inference import run_routed_inference
from utils.logging import (
    log_inference_completed,
    log_inference_started,
    log_inference_telemetry,
)

inference_logger = logging.getLogger("services.inference")


def handle_request(messages):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    prompt = messages[-1]["content"]
    inference_logger.info(f"[{request_id}] Prompt: {prompt}")

    # ---- ROUTING ----
    route_info = route_request(messages)

    selected_model = route_info.get("selected_model") or route_info.get("target_model")
    fallback_model = route_info.get("fallback_model")
    models_loaded_count = route_info.get("models_loaded", 1)
    chunk_strategy = route_info.get("chunk_strategy")

    inference_logger.info(f"[{request_id}] Selected model: {selected_model}")
    inference_logger.info(f"[{request_id}] Chunk strategy: {chunk_strategy}")
    inference_logger.info(f"[{request_id}] Models loaded: {models_loaded_count}")

    # ---- INFERENCE ----
    log_inference_started(
        model_name=selected_model,
        strategy=route_info.get("chunk_strategy"),
    )

    response = run_routed_inference(
        model_name=selected_model,
        messages=messages,
        routing=route_info,
    )

    latency = time.perf_counter() - start_time
    usage = response.get("usage", {}) if isinstance(response, dict) else {}

    log_inference_telemetry(
        model=selected_model,
        task_type=route_info.get("task_type"),
        strategy=route_info.get("chunk_strategy"),
        latency_seconds=latency,
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
        total_tokens=int(usage.get("total_tokens") or 0),
        models_used=response.get("models_used", [selected_model]),
        chunk_info=response.get("chunk_info"),
    )
    log_inference_completed(model_name=selected_model, latency_seconds=latency)

    inference_logger.info(
        f"[{request_id}] Completed request | "
        f"model={selected_model} "
        f"latency={latency:.2f}s"
    )

    return response.get("text", "")
