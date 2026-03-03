# backend/services/inference/llama.py
from typing import Any, Dict, List
from backend.config import MODEL_CONFIG
from backend.model.registry import get_model
from backend.utils.normalization import normalize_history_for_model


def _generate_with_model(
    model_name: str,
    messages: List[Dict[str, str]],
    max_tokens: int | None = None,
) -> Dict[str, Any]:
    normalized = normalize_history_for_model(messages)
    if model_name not in MODEL_CONFIG:
        raise ValueError(f"Unknown model: {model_name}")

    def inference_fn(model):
        cfg = MODEL_CONFIG[model_name]
        output = model.create_chat_completion(
            messages=normalized,
            max_tokens=max_tokens if max_tokens is not None else cfg["max_tokens"],
            temperature=cfg["temperature"],
            top_p=cfg["top_p"],
            repeat_penalty=cfg.get("repeat_penalty", 1.1),
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

    return get_model(model_name, inference_fn)


def run_inference(model_name: str, messages: List[Dict[str, str]]):
    return _generate_with_model(model_name=model_name, messages=messages)
