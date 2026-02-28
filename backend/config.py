USE_GPU = True

N_GPU_LAYERS = -1

MODEL_SMALL_PATH = "models/JOSIE-4B-Instruct.Q4_K_M.gguf"
MODEL_MEDIUM_PATH = "models/JOSIE-4B-Instruct.Q4_K_M.gguf"
MODEL_LARGE_PATH = "models/qwen2.5-coder-7b-instruct-q4_k_m-00001-of-00002.gguf"

SAFE_CTX_SMALL = 4096
SAFE_CTX_MEDIUM = 4096
SAFE_CTX_LARGE = 4096

TEMPERATURE_SMALL = 0
TEMPERATURE_MEDIUM = 0
TEMPERATURE_LARGE = 0

MAX_TOKENS_SMALL = 500
MAX_TOKENS_MEDIUM = 900
MAX_TOKENS_LARGE = 2000

TOP_P_SMALL = 0.5
TOP_P_MEDIUM = 0.5
TOP_P_LARGE = 0.5

SMALL_INPUT_BUDGET = SAFE_CTX_SMALL - MAX_TOKENS_SMALL - 300
MEDIUM_INPUT_BUDGET = SAFE_CTX_MEDIUM - MAX_TOKENS_MEDIUM - 400
LARGE_INPUT_BUDGET = SAFE_CTX_LARGE - MAX_TOKENS_LARGE - 400


MODEL_CONFIG = {
    "small": {
        "path": MODEL_SMALL_PATH,
        "n_gpu_layers": -1,
        "n_ctx": SAFE_CTX_SMALL,
        "max_tokens": MAX_TOKENS_SMALL,
        "temperature": TEMPERATURE_SMALL,
        "top_p": TOP_P_SMALL,
    },
    "medium": {
        "path": MODEL_MEDIUM_PATH,
        "n_gpu_layers": 40,
        "n_ctx": SAFE_CTX_MEDIUM,
        "max_tokens": MAX_TOKENS_MEDIUM,
        "temperature": TEMPERATURE_MEDIUM,
        "top_p": TOP_P_MEDIUM,
    },
    "large": {
        "path": MODEL_LARGE_PATH,
        "n_gpu_layers": 25,
        "n_ctx": SAFE_CTX_LARGE,
        "max_tokens": MAX_TOKENS_LARGE,
        "temperature": TEMPERATURE_LARGE,
        "top_p": TOP_P_LARGE,
    },
}

ROUTER_LIGHT_THRESHOLD = 800
ROUTER_HEAVY_THRESHOLD = 1500
