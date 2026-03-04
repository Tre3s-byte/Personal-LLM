from pathlib import Path
import os

# ============================================================
# PATHS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DOWNLOAD_FOLDER = os.path.join(os.environ.get("USERPROFILE", str(BASE_DIR)), "Music")

RAG_PATHS = [Path("C:/Users/maxim")]
RAG_INDEX_PATH = str(DATA_DIR / "faiss_index.index")
RAG_DOCS_PATH = str(DATA_DIR / "faiss_index.docs.json")

INDEX_PATH = "vector_store/index.faiss"
EMBEDDINGS_PATH = "vector_store/embeddings.pkl"

SQL_BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = SQL_BASE_DIR / "db" / "metadata.sqlite"
DATABASE_URL = f"sqlite:///{DB_PATH}"

MODEL_SMALL_PATH = "models/JOSIE-4B-Instruct.Q4_K_M.gguf"
MODEL_MEDIUM_PATH = "models/JOSIE-4B-Instruct.Q4_K_M.gguf"
MODEL_LARGE_PATH = "models/qwen2.5-coder-7b-instruct-q4_k_m-00001-of-00002.gguf"

# ============================================================
# SETTINGS
# ============================================================
USE_GPU = True
N_GPU_LAYERS = -1

SAFE_CTX_SMALL = 4096
SAFE_CTX_MEDIUM = 4096
SAFE_CTX_LARGE = 4096

TEMPERATURE_SMALL = 0.6
TEMPERATURE_MEDIUM = 0.2
TEMPERATURE_LARGE = 0

MAX_TOKENS_SMALL = 180
MAX_TOKENS_MEDIUM = 900
MAX_TOKENS_LARGE = 2000

TOP_P_SMALL = 0.9
TOP_P_MEDIUM = 0.5
TOP_P_LARGE = 0.5

PENALTY_SMALL = 1.2
PENALTY_MEDIUM = 1.08
PENALTY_LARGE = 1.05

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
        "repeat_penalty": PENALTY_SMALL,
    },
    "medium": {
        "path": MODEL_MEDIUM_PATH,
        "n_gpu_layers": 41,
        "n_ctx": SAFE_CTX_MEDIUM,
        "max_tokens": MAX_TOKENS_MEDIUM,
        "temperature": TEMPERATURE_MEDIUM,
        "top_p": TOP_P_MEDIUM,
        "repeat_penalty": PENALTY_MEDIUM,
    },
    "large": {
        "path": MODEL_LARGE_PATH,
        "n_gpu_layers": 25,
        "n_ctx": SAFE_CTX_LARGE,
        "max_tokens": MAX_TOKENS_LARGE,
        "temperature": TEMPERATURE_LARGE,
        "top_p": TOP_P_LARGE,
        "repeat_penalty": PENALTY_LARGE,
    },
}

RAG_CHUNK_SIZE = 1000
RAG_CHUNK_OVERLAP = 200
RAG_TOP_K = 4
RAG_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

MAX_FILE_SIZE_MB = 20
SECRET_PATTERNS = [
    r"api[_-]?key",
    r"secret",
    r"token",
    r"password",
    r"private[_-]?key",
    r"BEGIN RSA PRIVATE KEY",
    r"BEGIN OPENSSH PRIVATE KEY",
]

ROUTER_LIGHT_THRESHOLD = 800
ROUTER_HEAVY_THRESHOLD = 1500

EXCLUDED_DIRS = {
    "venv",
    ".venv",
    "node_modules",
    ".git",
    "__pycache__",
    ".anaconda",
    "anaconda3",
    ".cache",
    ".ollama",
    "OneDrive",
    "AppData",
}
