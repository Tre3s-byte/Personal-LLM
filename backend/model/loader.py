from llama_cpp import Llama
from pathlib import Path

_llm = None


def get_model():
    global _llm

    if _llm is None:
        base_dir = Path(__file__).resolve().parents[2]
        model_path = (
            base_dir
            / "backend"
            / "models"
            / "qwen2.5-7b-instruct-q5_k_m-00001-of-00002.gguf"
        )

        _llm = Llama(
            model_path=str(model_path),
            n_gpu_layers=-1,
            n_ctx=8192,
            n_batch=1024,
            n_threads=8,
            verbose=False,
        )

    return _llm
