"""Model registry that lazily initializes and unloads model instances."""

from pathlib import Path
from threading import Lock

from .loader import load_model, unload_model
from config import MODEL_CONFIG


BASE_DIR = Path(__file__).resolve().parents[2]
_MODEL_LOCK = Lock()


def get_model(name: str, inference_fn):
    """
    Load model, run inference_fn(model), then unload model.
    Thread-safe.
    """
    if name not in MODEL_CONFIG:
        raise ValueError(f"Unknown model: {name}")

    config = MODEL_CONFIG[name]
    model_path = BASE_DIR / "backend" / config["path"]

    with _MODEL_LOCK:
        model = load_model(
            model_path=str(model_path),
            n_gpu_layers=int(config["n_gpu_layers"]),
            n_ctx=int(config["n_ctx"]),
        )
        try:
            return inference_fn(model)
        finally:
            unload_model(model)
