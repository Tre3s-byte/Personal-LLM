#!/usr/bin/env bash

set -e

REQUIRED_MAJOR=3
REQUIRED_MINOR=10
PYTHON_BIN="python3.10"

echo "Checking for Python 3.10..."

if ! command -v $PYTHON_BIN &> /dev/null; then
    echo "Error: Python 3.10 is not installed or not in PATH."
    echo "Please install Python 3.10 and try again."
    exit 1
fi

# Obtener versión
PY_VERSION=$($PYTHON_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

if [ "$PY_VERSION" != "$REQUIRED_MAJOR.$REQUIRED_MINOR" ]; then
    echo "Error: Python 3.10 required. Found $PY_VERSION"
    exit 1
fi

echo ""
echo "Select installation type:"
echo "1) CPU"
echo "2) GPU (CUDA 12.1)"
read -p "Enter choice [1-2]: " INSTALL_TYPE

if [ "$INSTALL_TYPE" = "1" ]; then
    REQUIREMENTS_FILE="requirements.cpu.txt"
    echo "CPU mode selected."
elif [ "$INSTALL_TYPE" = "2" ]; then
    REQUIREMENTS_FILE="requirements.gpu.txt"
    echo "GPU mode selected."
else
    echo "Invalid selection."
    exit 1
fi


echo "Creating project structure..."

PROJECT_NAME="personal-llm-backend"
PYTHON_VERSION="3.10"

mkdir -p $PROJECT_NAME
cd $PROJECT_NAME

# Detect Linux and install build dependencies for pyenv



# Core structure
mkdir -p backend/app
mkdir -p backend/model
mkdir -p backend/api
mkdir -p backend/services
mkdir -p backend/utils
mkdir -p models
mkdir -p chats

# Base files
touch backend/app/main.py
touch backend/config.py
touch backend/model/loader.py
touch backend/model/downloader.py
touch backend/api/routes.py
touch backend/services/inference.py
touch backend/utils/device.py
touch backend/utils/logging.py

touch requirements.base.txt
touch requirements.gpu.txt
touch requirements.cpu.txt
touch README.md
touch .gitignore
touch .python-version

echo "$PYTHON_VERSION" > .python-version

echo "Creating virtual environment..."

if command -v pyenv &> /dev/null; then
    pyenv install -s $PYTHON_VERSION
    pyenv local $PYTHON_VERSION
    python -m venv .venv
else
    echo "pyenv not found. Using system python."
    $PYTHON_BIN -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip || true

cat <<EOF > .gitignore
.venv/
__pycache__/
*.pyc
models/
chats/
.env
EOF

echo "Writing requirements files..."

cat <<EOF > requirements.base.txt
fastapi
uvicorn
pydantic
python-dotenv
huggingface_hub
EOF

cat <<EOF > requirements.cpu.txt
-r requirements.base.txt
llama-cpp-python
EOF

cat <<EOF > requirements.gpu.txt
-r requirements.base.txt
llama-cpp-python-cu121
EOF

echo "Installing dependencies..."
pip install -r $REQUIREMENTS_FILE


echo "Backend scaffold complete."
echo ""
echo "Setup complete."
echo "Activate later with:"
echo "source .venv/bin/activate"