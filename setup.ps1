$ErrorActionPreference = "Stop"

$REQUIRED_MAJOR = 3
$REQUIRED_MINOR = 10
$PYTHON_BIN = "python"

Write-Host "Checking for Python 3.10..."

if (-not (Get-Command $PYTHON_BIN -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python 3.10 is not installed or not in PATH."
    Write-Host "Please install Python 3.10 and try again."
    exit 1
}

$PY_VERSION = & $PYTHON_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"

if ($PY_VERSION -ne "$REQUIRED_MAJOR.$REQUIRED_MINOR") {
    Write-Host "Error: Python 3.10 required. Found $PY_VERSION"
    exit 1
}

Write-Host "Creating project structure..."

$PROJECT_NAME = "personal-llm-backend"
$PYTHON_VERSION = "3.10"

New-Item -ItemType Directory -Force -Path $PROJECT_NAME | Out-Null
Set-Location $PROJECT_NAME

# Core structure
$dirs = @(
    "backend/app",
    "backend/model",
    "backend/api",
    "backend/services",
    "backend/utils",
    "models",
    "chats"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

# Base files
$files = @(
    "backend/app/main.py",
    "backend/config.py",
    "backend/model/loader.py",
    "backend/model/downloader.py",
    "backend/api/routes.py",
    "backend/services/inference.py",
    "backend/utils/device.py",
    "backend/utils/logging.py",
    "requirements.base.txt",
    "requirements.gpu.txt",
    "requirements.cpu.txt",
    "README.md",
    ".gitignore",
    ".python-version"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}

Set-Content -Path ".python-version" -Value $PYTHON_VERSION

Write-Host "Creating virtual environment..."

if (Get-Command pyenv -ErrorAction SilentlyContinue) {
    pyenv install -s $PYTHON_VERSION
    pyenv local $PYTHON_VERSION
    python -m venv .venv
} else {
    Write-Host "pyenv not found. Using system python."
    & $PYTHON_BIN -m venv .venv
}

Write-Host "Activating virtual environment..."
& ".\.venv\Scripts\Activate.ps1"

Write-Host "Upgrading pip..."
pip install --upgrade pip

Write-Host "Writing .gitignore..."

@"
.venv/
__pycache__/
*.pyc
models/
chats/
.env
"@ | Set-Content ".gitignore"

Write-Host "Base requirements..."

@"
gradio
llama-cpp-python
huggingface_hub
python-dotenv
"@ | Set-Content "requirements.base.txt"

"-r requirements.base.txt" | Set-Content "requirements.gpu.txt"
"-r requirements.base.txt" | Set-Content "requirements.cpu.txt"

Write-Host "Installing base dependencies..."
pip install -r requirements.base.txt

Write-Host ""
Write-Host "Backend scaffold complete."
Write-Host "Setup complete."
Write-Host "Activate later with:"
Write-Host ".\.venv\Scripts\Activate.ps1"