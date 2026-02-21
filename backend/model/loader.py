from llama_cpp import Llama
from pathlib import Path

#This function loads the model and make it available to generate the answers of every request
_llm = None


def load_model(model_path, n_gpu_layers, n_ctx):
    return Llama(
        model_path = model_path,
        n_gpu_layers = n_gpu_layers,
        n_ctx = n_ctx,
        n_batch = 256,
         n_threads=8,
         verbose = False
    )

# def get_model():
#     global _llm

#     if _llm is None:
#         base_dir = Path(__file__).resolve().parents[2]
#         model_path = (
#             base_dir
#             / "backend"
#             / "models"
#             / "qwen2.5-7b-instruct-q5_k_m-00001-of-00002.gguf"
#         )

#         _llm = Llama(
#             model_path=str(model_path),
#             n_gpu_layers=20,
#             n_ctx=4096,
#             n_batch=256,
#             n_threads=8,
#             verbose=False,
#         )

#     return _llm
