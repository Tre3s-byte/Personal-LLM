from typing import Any, Dict, List
import logging
import time

from config import MODEL_CONFIG
from model.registry import get_model
from services.chunker import chunk_code, chunk_log_text, trim_chat_history
from utils.normalization import normalize_history_for_model

logger = logging.getLogger("inference")
telemetry_logger = logging.getLogger("telemetry")


def _generate_with_model(
    model_name: str, messages: List[Dict[str, str]], max_tokens: int | None = None
) -> Dict[str, Any]:
    if model_name not in MODEL_CONFIG:
        raise ValueError(f"Unknown model: {model_name}")

    cfg = MODEL_CONFIG[model_name]
    model = get_model(model_name)
    normalized = normalize_history_for_model(messages)

    output = model.create_chat_completion(
        messages=normalized,
        max_tokens=max_tokens if max_tokens is not None else cfg["max_tokens"],
        temperature=cfg["temperature"],
        top_p=cfg["top_p"],
    )

    usage = output.get("usage") or {}
    text = output["choices"][0]["message"]["content"].strip()

    return {
        "text": text,
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        },
    }


def run_inference(model_name: str, messages: List[Dict[str, str]]):
    logger.info(f"Starting inference for model: {model_name}")
    start_time = time.time()

    response = _generate_with_model(model_name=model_name, messages=messages)

    processing_time = time.time() - start_time
    logger.info(
        f"Inference completed for model: {model_name}, processing time: {processing_time:.2f} seconds"
    )

    return response


def _extract_latest_user_text(messages: List[Dict[str, str]]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def _hierarchical_log_generate(model_name: str, messages: List[Dict[str, str]]) -> str:
    latest_text = _extract_latest_user_text(messages)
    chunks = chunk_log_text(latest_text, max_tokens=1000)

    if not chunks:
        return run_inference(model_name, messages)

    chunk_summaries = []
    models_used = [model_name]
    aggregate_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    for i, chunk in enumerate(chunks, start=1):
        prompt_messages = [
            {
                "role": "system",
                "content": "Summarize technical logs. Keep root causes, errors, and timestamps.",
            },
            {"role": "user", "content": f"Chunk {i}/{len(chunks)}\n\n{chunk}"},
        ]
        output = _generate_with_model(model_name, prompt_messages, max_tokens=350)
        chunk_summaries.append(output["text"])
        usage = output.get("usage", {})
        for key in aggregate_usage:
            aggregate_usage[key] += usage.get(key) or 0

    merge_messages = [
        {
            "role": "system",
            "content": "Merge chunk summaries into one coherent report with key findings and action items.",
        },
        {"role": "user", "content": "\n\n".join(chunk_summaries)},
    ]
    merged_output = _generate_with_model(model_name, merge_messages, max_tokens=500)
    merged_usage = merged_output.get("usage", {})
    for key in aggregate_usage:
        aggregate_usage[key] += merged_usage.get(key) or 0

    return {
        "text": merged_output["text"],
        "usage": aggregate_usage,
        "models_used": models_used,
        "chunk_info": {
            "chunk_count": len(chunks),
            "chunk_size": 1000,
            "chunk_strategy": "log",
        },
    }


def _structured_code_generate(model_name: str, messages: List[Dict[str, str]]) -> str:
    latest_text = _extract_latest_user_text(messages)
    code_chunks = chunk_code(latest_text, max_tokens=900)

    if not code_chunks:
        return run_inference(model_name, messages)

    function_summaries = []
    models_used = [model_name]
    aggregate_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    for i, chunk in enumerate(code_chunks, start=1):
        prompt_messages = [
            {
                "role": "system",
                "content": "Summarize this code block: purpose, dependencies, and potential issues.",
            },
            {
                "role": "user",
                "content": f"Code block {i}/{len(code_chunks)}\n\n{chunk}",
            },
        ]
        output = _generate_with_model(model_name, prompt_messages, max_tokens=300)
        function_summaries.append(output["text"])
        usage = output.get("usage", {})
        for key in aggregate_usage:
            aggregate_usage[key] += usage.get(key) or 0

    reasoning_messages = [
        {
            "role": "system",
            "content": "Reason about the program using block summaries. Mention which full blocks should be inspected next if needed.",
        },
        {"role": "user", "content": "\n\n".join(function_summaries)},
    ]
    reasoning_output = _generate_with_model(model_name, reasoning_messages, max_tokens=700)
    reasoning_usage = reasoning_output.get("usage", {})
    for key in aggregate_usage:
        aggregate_usage[key] += reasoning_usage.get(key) or 0

    return {
        "text": reasoning_output["text"],
        "usage": aggregate_usage,
        "models_used": models_used,
        "chunk_info": {
            "chunk_count": len(code_chunks),
            "chunk_size": 900,
            "chunk_strategy": "code",
        },
    }


def run_routed_inference(
    model_name: str, messages: List[Dict[str, str]], routing: Dict[str, str]
):
    start_time = time.time()
    logger.info(
        f"Starting routed inference | model={model_name} strategy={routing.get('chunk_strategy')}"
    )

    strategy = routing.get("chunk_strategy")

    if strategy == "chat":
        cfg = MODEL_CONFIG[model_name]
        safe_input_budget = int(cfg["n_ctx"] * 0.85)
        trimmed_messages = trim_chat_history(messages, max_tokens=safe_input_budget)
        response = run_inference(model_name, trimmed_messages)
        chunk_info = {
            "chunk_count": 1,
            "chunk_size": safe_input_budget,
            "chunk_strategy": "chat_trim",
        }

    elif strategy == "log":
        response = _hierarchical_log_generate(model_name, messages)
        chunk_info = response.get("chunk_info")

    elif strategy == "code":
        response = _structured_code_generate(model_name, messages)
        chunk_info = response.get("chunk_info")

    else:
        response = run_inference(model_name, messages)
        chunk_info = {
            "chunk_count": 1,
            "chunk_size": None,
            "chunk_strategy": "none",
        }

    latency = time.time() - start_time

    usage = response.get("usage") if isinstance(response, dict) else None
    prompt_tokens = usage.get("prompt_tokens") if usage else None
    completion_tokens = usage.get("completion_tokens") if usage else None
    total_tokens = usage.get("total_tokens") if usage else None
    tokens_per_second = None
    if total_tokens and latency > 0:
        tokens_per_second = total_tokens / latency

    models_used = response.get("models_used", [model_name]) if isinstance(response, dict) else [model_name]

    telemetry_payload = {
        "event": "inference_complete",
        "model": model_name,
        "models_used": models_used,
        "task_type": routing.get("task_type"),
        "strategy": strategy,
        "latency_seconds": round(latency, 4),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "tokens_per_second": round(tokens_per_second, 4) if tokens_per_second else None,
        "chunk_info": chunk_info,
    }
    telemetry_logger.info("", extra={"event_payload": telemetry_payload})
    logger.info(
        f"Completed routed inference | model={model_name} latency={latency:.2f}s"
    )

    return response["text"] if isinstance(response, dict) else response
