from typing import Any, Dict, List

from config import MODEL_CONFIG
from model.registry import get_model
from services.chunker import chunk_code, chunk_log_text, trim_chat_history
from utils.normalization import normalize_history_for_model


# ------------------------
# Core generation
# ------------------------


def _generate_with_model(
    model_name: str,
    messages: List[Dict[str, str]],
    max_tokens: int | None = None,
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

    prompt_tokens = usage.get("prompt_tokens") or 0
    completion_tokens = usage.get("completion_tokens") or 0
    total_tokens = usage.get("total_tokens") or (prompt_tokens + completion_tokens)

    text = output["choices"][0]["message"]["content"].strip()

    return {
        "text": text,
        "usage": {
            "prompt_tokens": int(prompt_tokens),
            "completion_tokens": int(completion_tokens),
            "total_tokens": int(total_tokens),
        },
    }


def run_inference(model_name: str, messages: List[Dict[str, str]]):
    return _generate_with_model(model_name=model_name, messages=messages)


# ------------------------
# Chunk helpers
# ------------------------


def _extract_latest_user_text(messages: List[Dict[str, str]]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def _aggregate_usage(aggregate: Dict[str, int], usage: Dict[str, int]):
    for key in aggregate:
        aggregate[key] += int(usage.get(key) or 0)


# ------------------------
# Log strategy
# ------------------------


def _hierarchical_log_generate(model_name: str, messages: List[Dict[str, str]]):

    latest_text = _extract_latest_user_text(messages)
    chunks = chunk_log_text(latest_text, max_tokens=1000)

    if not chunks:
        return run_inference(model_name, messages)

    aggregate_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }

    chunk_summaries = []

    for i, chunk in enumerate(chunks, start=1):
        prompt_messages = [
            {
                "role": "system",
                "content": "Summarize technical logs. Keep root causes, errors, timestamps.",
            },
            {"role": "user", "content": f"Chunk {i}/{len(chunks)}\n\n{chunk}"},
        ]

        output = _generate_with_model(model_name, prompt_messages, max_tokens=350)
        chunk_summaries.append(output["text"])
        _aggregate_usage(aggregate_usage, output["usage"])

    merge_messages = [
        {
            "role": "system",
            "content": "Merge summaries into a coherent report with key findings.",
        },
        {"role": "user", "content": "\n\n".join(chunk_summaries)},
    ]

    merged_output = _generate_with_model(model_name, merge_messages, max_tokens=500)
    _aggregate_usage(aggregate_usage, merged_output["usage"])

    return {
        "text": merged_output["text"],
        "usage": aggregate_usage,
        "models_used": [model_name],
        "chunk_info": {
            "chunk_count": len(chunks),
            "chunk_size": 1000,
            "chunk_strategy": "log",
        },
    }


# ------------------------
# Code strategy
# ------------------------


def _structured_code_generate(model_name: str, messages: List[Dict[str, str]]):

    latest_text = _extract_latest_user_text(messages)
    code_chunks = chunk_code(latest_text, max_tokens=900)

    if not code_chunks:
        return run_inference(model_name, messages)

    aggregate_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }

    function_summaries = []

    for i, chunk in enumerate(code_chunks, start=1):
        prompt_messages = [
            {"role": "system", "content": "Summarize this code block."},
            {"role": "user", "content": f"Block {i}/{len(code_chunks)}\n\n{chunk}"},
        ]

        output = _generate_with_model(model_name, prompt_messages, max_tokens=300)
        function_summaries.append(output["text"])
        _aggregate_usage(aggregate_usage, output["usage"])

    reasoning_messages = [
        {"role": "system", "content": "Reason about the program using summaries."},
        {"role": "user", "content": "\n\n".join(function_summaries)},
    ]

    reasoning_output = _generate_with_model(
        model_name, reasoning_messages, max_tokens=700
    )
    _aggregate_usage(aggregate_usage, reasoning_output["usage"])

    return {
        "text": reasoning_output["text"],
        "usage": aggregate_usage,
        "models_used": [model_name],
        "chunk_info": {
            "chunk_count": len(code_chunks),
            "chunk_size": 900,
            "chunk_strategy": "code",
        },
    }


# ------------------------
# Routed inference
# ------------------------


def run_routed_inference(
    model_name: str,
    messages: List[Dict[str, str]],
    routing: Dict[str, Any],
):
    strategy = routing.get("chunk_strategy")

    if strategy == "chat":
        cfg = MODEL_CONFIG[model_name]
        safe_input_budget = int(cfg["n_ctx"] * 0.85)
        trimmed = trim_chat_history(messages, max_tokens=safe_input_budget)
        response = run_inference(model_name, trimmed)
        chunk_info = {
            "chunk_count": 1,
            "chunk_size": safe_input_budget,
            "chunk_strategy": "chat_trim",
        }

    elif strategy == "log":
        response = _hierarchical_log_generate(model_name, messages)
        chunk_info = response.get("chunk_info", {})

    elif strategy == "code":
        response = _structured_code_generate(model_name, messages)
        chunk_info = response.get("chunk_info", {})

    else:
        response = run_inference(model_name, messages)
        chunk_info = {
            "chunk_count": 1,
            "chunk_size": None,
            "chunk_strategy": "none",
        }


    if isinstance(response, dict):
        response.setdefault("models_used", [model_name])
        response.setdefault("chunk_info", chunk_info)
        return response

    return {
        "text": response,
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
        "models_used": [model_name],
        "chunk_info": chunk_info,
    }
