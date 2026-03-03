"""Low-level model loader for llama.cpp GGUF backends."""

from llama_cpp import Llama
import os
import gc

# This function loads the model and make it available to generate the answers of every request
_llm = None


def load_model(model_path, n_gpu_layers, n_ctx):
    global _llm
    _llm = Llama(
        model_path=model_path,
        n_gpu_layers=n_gpu_layers,
        n_ctx=n_ctx,
        n_batch=512,
        n_threads=max(1, os.cpu_count() - 2),
        verbose=False,
        backend="cuda",
    )
    print(f"[LOAD] Modelo cargado desde: {model_path}")
    return _llm


def unload_model(model):
    """
    Explicitly free llama.cpp native memory.
    """
    global _llm
    try:
        del model
        _llm = None
        print("[UNLOAD] Modelo descargado y referencias eliminadas")
    except Exception:
        pass
    gc.collect()

    try:
        import torch

        if torch.cuda.is_avaible():
            torch.cuda.empty_cache()
            print("[UNLOAD] Memoria CUDA liberada")
    except Exception:
        pass
