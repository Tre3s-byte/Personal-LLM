import logging
import uuid
import time
import json
from services.router import route_request

inference_logger = logging.getLogger("inference")
telemetry_logger = logging.getLogger("telemetry")

request_id = str(uuid.uuid4())
start_time = time.perf_counter()

prompt = messages[-1]["content"]
inference_logger.info(f"[{request_id}] Prompt: {prompt}")

# ---- ROUTING ----
route_info = route_request(messages)

selected_model = route_info["selected_model"]
fallback_model = route_info.get("fallback_model")
models_loaded_count = route_info.get("models_loaded", 1)
chunking_enabled = route_info.get("needs_chunking", False)

inference_logger.info(f"[{request_id}] Selected model: {selected_model}")
inference_logger.info(f"[{request_id}] Chunking enabled: {chunking_enabled}")

# ---- TOKEN COUNT BEFORE ----
original_tokens_count = count_tokens(prompt, selected_model)

# ---- CHUNKING ----
if chunking_enabled:
    chunks, chunk_meta = chunk_prompt(prompt, selected_model)
    num_chunks = len(chunks)
    tokens_per_chunk = chunk_meta["tokens_per_chunk"]
    overlap_size = chunk_meta.get("overlap", 0)
    max_context = chunk_meta["max_context"]
else:
    chunks = [prompt]
    num_chunks = 1
    tokens_per_chunk = original_tokens_count
    overlap_size = 0
    max_context = get_model_context(selected_model)

# ---- GENERATION ----
full_output = ""
output_tokens = 0

for chunk in chunks:
    result = generate_with_model(selected_model, chunk)

    full_output += result["text"]
    output_tokens += result["output_tokens"]

input_tokens = original_tokens_count

# ---- FINAL METRICS ----
end_time = time.perf_counter()
latency = end_time - start_time
tokens_per_second = output_tokens / latency if latency > 0 else 0

# ---- TELEMETRY ----
telemetry_payload = {
    "event": "inference_complete",
    "request_id": request_id,
    "routing": {
        "selected_model": selected_model,
        "fallback_model": fallback_model,
        "models_loaded": models_loaded_count,
    },
    "chunking": {
        "enabled": chunking_enabled,
        "original_tokens": original_tokens_count,
        "max_context": max_context,
        "num_chunks": num_chunks,
        "tokens_per_chunk": tokens_per_chunk,
        "overlap": overlap_size,
    },
    "tokens": {
        "input": input_tokens,
        "output": output_tokens,
        "total": input_tokens + output_tokens,
        "tokens_per_second": tokens_per_second,
    },
    "timing": {"latency_seconds": latency},
}

telemetry_logger.info(json.dumps(telemetry_payload))

inference_logger.info(
    f"[{request_id}] Completed | "
    f"in={input_tokens} out={output_tokens} "
    f"latency={latency:.2f}s tps={tokens_per_second:.2f}"
)
