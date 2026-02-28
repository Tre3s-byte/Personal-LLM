import uuid
import time

from services.router import route_request
from services.inference import run_routed_inference
from utils.logging import setup_logging

app_logger, inference_logger, telemetry_logger = setup_logging()


def handle_request(messages):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    prompt = messages[-1]["content"]

    # ---- REQUEST RECEIVED ----
    inference_logger.info(
        "Request received",
        extra={"extra_data": {"request_id": request_id, "event": "request_received"}},
    )

    app_logger.info(
        "Prompt captured",
        extra={
            "extra_data": {
                "request_id": request_id,
                "prompt": prompt,
                "messages": messages,
            }
        },
    )

    # ---- ROUTING ----
    route_info = route_request(messages)

    selected_model = route_info.get("selected_model") or route_info.get("target_model")
    fallback_model = route_info.get("fallback_model")
    models_loaded_count = route_info.get("models_loaded", 1)
    chunk_strategy = route_info.get("chunk_strategy")

    app_logger.info(
        "Routing completed",
        extra={
            "extra_data": {
                "request_id": request_id,
                "selected_model": selected_model,
                "fallback_model": fallback_model,
                "models_loaded": models_loaded_count,
                "chunk_strategy": chunk_strategy,
                "task_type": route_info.get("task_type"),
            }
        },
    )

    # ---- INFERENCE ----
    response = run_routed_inference(
        model_name=selected_model,
        messages=messages,
        routing=route_info,
    )

    inference_process_time = time.perf_counter() - start_time

    if isinstance(response, dict):
        usage = response.get("usage", {})
        response_text = response.get("text", "")
        models_used = response.get("models_used", [selected_model])
        chunk_info = response.get("chunk_info")
    else:
        usage = {}
        response_text = str(response)
        models_used = [selected_model]
        chunk_info = None

    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or 0)
    tokens_per_second = (
        total_tokens / inference_process_time if inference_process_time > 0 else 0
    )

    # ---- RESPONSE GENERATED ----
    inference_logger.info(
        "Response generated",
        extra={"extra_data": {"request_id": request_id, "event": "response_generated"}},
    )

    telemetry_logger.info(
        "Inference telemetry",
        extra={
            "extra_data": {
                "request_id": request_id,
                "model_used": str(selected_model),
                "models_involved": models_used,
                "task_type": route_info.get("task_type"),
                "inference_process_time": inference_process_time,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "tokens_per_second": tokens_per_second,
                "chunk_info": chunk_info,
            }
        },
    )

    # ---- FULL TRACE ----
    app_logger.info(
        "Inference completed",
        extra={
            "extra_data": {
                "request_id": request_id,
                "prompt": prompt,
                "response": response_text,
                "model_used": str(selected_model),
                "models_involved": models_used,
                "chunk_strategy": chunk_strategy,
                "chunk_info": chunk_info,
                "inference_process_time": inference_process_time,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "tokens_per_second": tokens_per_second,
            }
        },
    )

    return response_text
