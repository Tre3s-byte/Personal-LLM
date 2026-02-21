USE_GPU = True
N_GPU_LAYERS = -1
SAFE_CTX_SMALL = 2048
SAFE_CTX_MEDIUM = 4096
SAFE_CTX_LARGE = 4096

MODEL_SMALL_PATH = "models/qwen-1.5b-q4.gguf"
MODEL_MEDIUM_PATH = "models/phi3-mini.gguf"
MODEL_LARGE_PATH = "models/qwen2.5-7b-instruct-q5_k_m.gguf"

MODE_CONFIG = {
    "small":{
        "path": MODEL_SMALL_PATH,
        "n_gpu_layers": "-1",
        "n_ctx" : SAFE_CTX_SMALL
    },
    "medium":{
        "path": MODEL_MEDIUM_PATH,
        "n_gpu_layers": "30",
        "n_ctx" : SAFE_CTX_MEDIUM
    },
    "large":{
        "path": MODEL_LARGE_PATH,
        "n_gpu_layers": "20",
        "n_ctx" : SAFE_CTX_LARGE
    }
}