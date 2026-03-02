"""Model registry that lazily initializes and caches model instances."""

from pathlib import Path
from .loader import load_model
from config import MODEL_CONFIG

_model_cache = {}
BASE_DIR = Path(__file__).resolve().parents[2]  # Personal LLM/


def get_model(name: str):
    if name not in MODEL_CONFIG:
        raise ValueError(f"Unknown model:{name}")
    if name in _model_cache:
        return _model_cache[name]

    config = MODEL_CONFIG[name]

    base_dir = BASE_DIR  # noqa: F841
    model_path = BASE_DIR / "backend" / config["path"]  # noqa: F823

    model = load_model(
        model_path=str(model_path),
        n_gpu_layers=int(config["n_gpu_layers"]),
        n_ctx=int(config["n_ctx"]),
    )
    _model_cache[name] = model
    return model
