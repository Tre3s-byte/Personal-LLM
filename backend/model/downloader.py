import os
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BASE_DIR / "backend" / "models"
load_dotenv(BASE_DIR / ".env")
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found in environment variables.")

MODELS = {
    "large": {
        "repo_id": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
        "files": [
            "qwen2.5-coder-7b-instruct-q4_k_m-00001-of-00002.gguf",
            "qwen2.5-coder-7b-instruct-q4_k_m-00002-of-00002.gguf",
        ],
    },
    "medium": {
        "repo_id": "mradermacher/JOSIE-4B-Thinking-GGUF",
        "files": ["JOSIE-4B-Thinking.Q4_K_M.gguf"],
    },
    "small": {
        "repo_id": "mradermacher/JOSIE-4B-Instruct-GGUF",
        "files": ["JOSIE-4B-Instruct.Q4_K_M.gguf"],
    },
}


def download_model(model_name: str):
    if model_name not in MODELS:
        raise ValueError(f"Unknown model: {model_name}")

    model_info = MODELS[model_name]

    for filename in model_info["files"]:
        try:
            path = hf_hub_download(
                repo_id=model_info["repo_id"],
                filename=filename,
                local_dir=str(MODEL_DIR),
                local_dir_use_symlinks=False,
                token=HF_TOKEN,
            )
            print(f"[OK] {model_name} -> {filename}")
        except Exception as e:
            print(f"[ERROR] {model_name} -> {filename} -> {e}")


if __name__ == "__main__":
    for model in MODELS.keys():
        download_model(model)

# for fragment in fragments:
#     try:
#         path = hf_hub_download(
#             repo_id=,
#             filename=fragment,
#             local_dir=str(BASE_DIR / "backend" / "models"),
#             force_download=True,
#             local_dir_use_symlinks=False,
#             token=HF_TOKEN,
#         )
#         print(f"Downloaded {fragment} to {path}")
#     except Exception as e:
#         print(f"Error downloading {fragment}: {e}")
