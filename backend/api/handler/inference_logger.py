from backend.utils.logging import (
    log_inference_request,
    log_inference_response,
    log_inference_telemetry,
)
import logging


def log_request(request_id: str, prompt_text: str, model_name: str, strategy: str):
    log_inference_request(
        request_id=request_id,
        prompt=prompt_text,
        model_name=model_name,
        strategy=strategy,
    )


def log_response(request_id: str, response_text: str, model_name: str, latency: float):
    logger = logging.getLogger("services.inference")
    logger.info(
        "inference_response_generated",
        extra={
            "request_id": request_id,
            "response_text": response_text,
            "model_used": model_name,
            "inference_process_time": latency,
            "event": "response_generated",
        },
    )


def process_response(
    response: dict, request_id: str, model_name: str, task_type: str, latency: float
):
    usage = response.get("usage", {}) if isinstance(response, dict) else {}
    response_text = response.get("text", "")

    # Log response here
    log_response(request_id, response_text, model_name, latency)

    log_inference_telemetry(
        request_id=request_id,
        model_used=model_name,
        task_type=task_type,
        inference_process_time=latency,
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
        total_tokens=int(usage.get("total_tokens") or 0),
    )

    return response_text, usage
