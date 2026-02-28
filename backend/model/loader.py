from llama_cpp import Llama
from pathlib import Path  # noqa: F401
import os

# This function loads the model and make it available to generate the answers of every request
_llm = None


def load_model(model_path, n_gpu_layers, n_ctx):
    return Llama(
        model_path=model_path,
        n_gpu_layers=n_gpu_layers,
        n_ctx=n_ctx,
        n_batch=512,
        n_threads=os.cpu_count() - 2,
        verbose=True,
    )
