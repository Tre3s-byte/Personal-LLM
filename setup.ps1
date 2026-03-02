$ErrorActionPreference = "Stop"

$PROJECT_NAME = "personal-ai-assistant"
$ENV_NAME = "personal-ai"
$PYTHON_VERSION = "3.10"

Write-Host "Checking for Conda..."

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Conda is not installed or not in PATH."
    Write-Host "Install Miniconda or Anaconda and try again."
    exit 1
}

Write-Host "Creating project structure..."

New-Item -ItemType Directory -Force -Path $PROJECT_NAME | Out-Null
Set-Location $PROJECT_NAME

$dirs = @(
    "backend/app",
    "backend/api",
    "backend/model",
    "backend/services",
    "backend/rag",
    "backend/db",
    "backend/utils",
    "models",
    "data",
    "chats",
    "logs"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

$files = @(
    "backend/app/main.py",
    "backend/api/routes.py",
    "backend/model/loader.py",
    "backend/model/registry.py",
    "backend/services/inference.py",
    "backend/services/ingestion.py",
    "backend/rag/rag.py",
    "backend/db/models.py",
    "backend/config.py",
    "requirements.txt",
    "README.md",
    ".gitignore"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}

Write-Host "Creating Conda environment..."

conda create -y -n $ENV_NAME python=$PYTHON_VERSION

Write-Host "Activating environment..."
conda activate $ENV_NAME

Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

Write-Host "Writing requirements.txt..."

@"
accelerate==1.12.0
aiosqlite==0.22.1
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.12.1
click==8.3.1
diskcache==5.6.3
exceptiongroup==1.3.1
fastapi==0.129.0
filelock==3.24.3
fsspec==2026.2.0
greenlet==3.3.2
h11==0.16.0
hf-xet==1.2.0
hnswlib==0.8.0
httpcore==1.0.9
httpx==0.28.1
huggingface_hub==0.36.2
jinja2
joblib
llama_cpp_python==0.3.16
markdown-it-py==4.0.0
matplotlib==3.10.8
numpy==1.26.4
pandas
psutil
pydantic==2.12.5
PyPDF2==3.0.1
PySide6==6.9.2
python-dotenv==1.2.1
PyYAML
regex==2026.2.19
requests
rich==14.3.3
safetensors==0.7.0
scikit-learn
scipy
sentence-transformers==2.6.1
SQLAlchemy==2.0.47
starlette==0.52.1
sympy
tokenizers==0.15.2
torch==2.2.2
torchaudio==2.2.2
torchvision==0.17.2
tqdm
transformers==4.38.2
typer==0.24.0
typing-inspection==0.4.2
uvicorn==0.41.0
yt-dlp==2026.2.21
faiss-cpu
"@ | Set-Content "requirements.txt"

Write-Host "Installing dependencies..."
pip install -r requirements.txt

Write-Host "Writing .gitignore..."

@"
__pycache__/
*.pyc
.env
models/
data/
chats/
logs/
*.db
"@ | Set-Content ".gitignore"

Write-Host ""
Write-Host "Environment ready."
Write-Host "Activate later with:"
Write-Host "conda activate $ENV_NAME"
Write-Host ""
Write-Host "Run backend with:"
Write-Host "uvicorn backend.app.main:app --reload"