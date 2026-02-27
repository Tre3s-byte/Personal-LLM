import logging
import uuid
import time

from services.router import route_request
from services.inference import run_routed_inference

inference_logger = logging.getLogger("inference")


def handle_request(messages):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    prompt = messages[-1]["content"]
    inference_logger.info(f"[{request_id}] Prompt: {prompt}")

    # ---- ROUTING ----
    route_info = route_request(messages)

    selected_model = route_info.get("selected_model")
    fallback_model = route_info.get("fallback_model")
    models_loaded_count = route_info.get("models_loaded", 1)
    chunk_strategy = route_info.get("chunk_strategy")

    inference_logger.info(f"[{request_id}] Selected model: {selected_model}")
    inference_logger.info(f"[{request_id}] Chunk strategy: {chunk_strategy}")
    inference_logger.info(f"[{request_id}] Models loaded: {models_loaded_count}")

    # ---- INFERENCE ----
    response_text = run_routed_inference(
        model_name=selected_model,
        messages=messages,
        routing=route_info,
    )

    latency = time.perf_counter() - start_time

    inference_logger.info(
        f"[{request_id}] Completed request | "
        f"model={selected_model} "
        f"latency={latency:.2f}s"
    )

    return response_text
