# Personal AI Server

Self-hosted AI infrastructure for local LLM inference, retrieval-augmented generation (RAG), and secure remote access over a private network.

## What this project is

Personal AI Server is an **AI operating layer** for your workstation:
- Local LLM inference
- RAG over personal documents
- Secure file access and controlled system actions
- Remote API access via VPN

## Quick Start

1. Clone the repository:
   ```bash
   git clone <repo_url>
   cd Personal-LLM
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
   On Windows PowerShell:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
3. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.cpu.txt
   ```
4. Run the backend:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
5. Open API docs at `http://127.0.0.1:8000/docs`.

## Clean Developer Onboarding

If you're contributing or setting this up for the first time, follow this flow:

1. **Read architecture first**: start with [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
2. **Review contribution process**: read [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md).
3. **Review security expectations**: read [`docs/SECURITY.md`](docs/SECURITY.md).
4. **Set local configuration**:
   - Ensure your model backend is available (for example Ollama/local transformers).
   - Configure allowed filesystem paths and any auth settings before exposing endpoints.
5. **Run quality checks before committing**:
   - Python formatting/linting (if configured in your environment)
   - Backend smoke test by starting the app and opening `/docs`
6. **Develop in small slices**:
   - Keep service boundaries clear (`api` → `services` → `model/utils`).
   - Avoid bypassing validation in file and automation layers.

## Documentation

- Architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Contributing: [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)
- Security: [`docs/SECURITY.md`](docs/SECURITY.md)

## License

MIT (as indicated by project badge and repository metadata).
