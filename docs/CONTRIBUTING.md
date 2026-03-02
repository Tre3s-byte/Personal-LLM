# Contributing Guide

Thanks for contributing to Personal AI Server.

## Development Philosophy

- Keep modules small and explicit.
- Preserve layer boundaries (`api` -> `services` -> `model/utils`).
- Prefer safe defaults over convenience in security-sensitive areas.

## Local Setup

1. Create a virtual environment and install backend deps:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.cpu.txt
   ```
2. Run the backend:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
3. Confirm API is reachable at `http://127.0.0.1:8000/docs`.

## Branching and Commits

- Use a dedicated branch per change.
- Keep commits focused and descriptive.
- Write commit messages in imperative mood (e.g., `Add docs for architecture split`).

## Pull Request Expectations

- Clearly describe **what changed** and **why**.
- Include testing/verification steps.
- Note any security implications for API, file, or automation changes.
- Keep PR scope narrow when possible.

## Code and Review Checklist

Before opening a PR:

- [ ] Documentation updated when behavior changes.
- [ ] No hardcoded secrets, tokens, or private paths.
- [ ] File access remains restricted to allowed paths.
- [ ] Automation endpoints still execute only predefined actions.
- [ ] Basic run check completed (`uvicorn ...` and `/docs` loads).

## Documentation

For major architecture changes, update:
- `docs/ARCHITECTURE.md`
- `README.md` (if onboarding or quick-start flow changes)
