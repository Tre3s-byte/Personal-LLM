import os
import gc
import logging
from llama_cpp import Llama, llama_cpp

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

_llm = None


def _gpu_offload_supported() -> bool:
    """Return whether the installed llama.cpp runtime supports GPU offload."""
    try:
        return bool(llama_cpp.llama_supports_gpu_offload())
    except Exception:
        return False


def load_model(model_path, n_gpu_layers, n_ctx):
    global _llm
    gpu_supported = _gpu_offload_supported()
    effective_gpu_layers = n_gpu_layers if gpu_supported else 0

    if n_gpu_layers != 0 and not gpu_supported:
        logger.warning(
            "llama.cpp was built without GPU offload support. "
            "Model will run on CPU. Install backend/requirements.gpu.txt and rebuild the venv."
        )

    _llm = Llama(
        model_path=model_path,
        n_gpu_layers=effective_gpu_layers,
        n_ctx=n_ctx,
        n_batch=512,
        n_threads=max(1, os.cpu_count() - 2),
        verbose=False,
    )

    logger.info(
        f"Modelo cargado desde: {model_path} "
        f"(n_gpu_layers={effective_gpu_layers}, gpu_supported={gpu_supported})"
    )
    return _llm


def unload_model(model):
    """
    Explicitly free llama.cpp native memory.
    """
    global _llm
    try:
        del model
        _llm = None
        logger.info("Modelo descargado y referencias eliminadas")
    except Exception:
        pass

    gc.collect()

    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("Memoria CUDA liberada")
    except Exception:
        pass
