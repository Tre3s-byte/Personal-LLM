from pathlib import Path
from .loader import load_model
from config import MODEL_CONFIG

_models = {}



def get_model(name:str):
    if name in _models:
        return _models[name]

    if name not in MODEL_CONFIG:
        raise ValueError(f"Unknown model:{name}")
    
    config = MODEL_CONFIG[name]

    base_dir = Path(__file__).resolve().parents[2]
    model_path = base_dir / "backend" / config["path"]

    model = load_model(
        model_path = str(model_path),
        n_gpu_layers= config["n_gpu_layers"],
        n_ctx= config["n_ctx"]
    )
    _models[name] = model 
    return model