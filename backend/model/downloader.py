import os
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found in environment variables.")

fragments = [
    "qwen2.5-7b-instruct-q5_k_m-00001-of-00002.gguf",
    "qwen2.5-7b-instruct-q5_k_m-00002-of-00002.gguf",
]


for fragment in fragments:
    try:
        path = hf_hub_download(
            repo_id="Qwen/Qwen2.5-7B-Instruct-GGUF",
            filename=fragment,
            local_dir=str(BASE_DIR / "backend" / "models"),
            force_download=True,
            local_dir_use_symlinks=False,
            token=HF_TOKEN,
        )
        print(f"Downloaded {fragment} to {path}")
    except Exception as e:
        print(f"Error downloading {fragment}: {e}")
