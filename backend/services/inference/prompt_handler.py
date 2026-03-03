# backend/services/inference/prompt_handler.py
from typing import Any, Dict, List
from backend.services.chunker import chunk_code, chunk_log_text, trim_chat_history
from backend.services.inference.llama import run_inference, _generate_with_model
from backend.config import MODEL_CONFIG


def _extract_latest_user_text(messages: List[Dict[str, str]]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def _aggregate_usage(aggregate: Dict[str, int], usage: Dict[str, int]):
    for key in aggregate:
        aggregate[key] += int(usage.get(key) or 0)


def _hierarchical_log_generate(model_name: str, messages: List[Dict[str, str]]):
    latest_text = _extract_latest_user_text(messages)
    chunks = chunk_log_text(latest_text, max_tokens=1000)

    if not chunks:
        return run_inference(model_name, messages)

    aggregate_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
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


def _structured_code_generate(model_name: str, messages: List[Dict[str, str]]):
    latest_text = _extract_latest_user_text(messages)
    code_chunks = chunk_code(latest_text, max_tokens=900)

    if not code_chunks:
        return run_inference(model_name, messages)

    aggregate_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
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


def run_routed_inference(
    model_name: str, messages: List[Dict[str, str]], routing: Dict[str, Any]
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
        chunk_info = {"chunk_count": 1, "chunk_size": None, "chunk_strategy": "none"}

    if isinstance(response, dict):
        response.setdefault("models_used", [model_name])
        response.setdefault("chunk_info", chunk_info)
        return response

    return {
        "text": response,
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "models_used": [model_name],
        "chunk_info": chunk_info,
    }
