# Repository Guidelines

## Project Structure & Module Organization
Backend lives in `backend/`, with FastAPI entry point `backend/main.py` and domain modules in `backend/src/{api,ai,tarot,models,schemas,core}`. Unit tests sit in `backend/tests`, while migrations and prompts live in `backend/alembic` and `backend/prompts`. The Next.js client resides in `frontend/`; routes and layouts are in `frontend/src/app`, shared UI in `frontend/src/components`, utilities in `frontend/src/lib`, and static assets in `frontend/public`. Root docs cover architecture and deployment, and `deploy.sh` orchestrates combined releases.

## Build, Test, and Development Commands
```bash
# Backend setup & dev
python3 -m venv backend/venv && source backend/venv/bin/activate
pip install -r backend/requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
pytest
pytest --cov=src --cov-report=term-missing

# Frontend setup & dev
cd frontend && npm install
npm run dev
npm run build && npm run start
npm run lint && npm run format
```

## Coding Style & Naming Conventions
Use Black (line length 88) and isort for Python; keep modules, functions, and variables snake_case and classes PascalCase. Keep FastAPI route paths human-readable and map them to explicit Pydantic schema names. Apply type hints across `backend/src`, especially on provider interfaces. The frontend follows ESLint + Prettier defaults (2-space indent); prefer functional React components, suffix custom hooks with `use`, and place reusable UI in `frontend/src/components`. Mirror existing folder boundaries (`tarot/`, `providers/`, `types/`) when adding files.

## Testing Guidelines
Write pytest modules that mirror the package under test (e.g., `tests/test_response_parser.py` for `src/ai`). Extend scenario scripts such as `backend/test_enhanced_reading.py` when validating new spreads or providers. Capture shared fixtures in `backend/tests/conftest.py` as complexity grows and target ≥80% coverage with `pytest --cov`. The frontend currently relies on linting and manual QA; add Testing Library or Playwright regression suites when expanding interactive flows.

## Commit & Pull Request Guidelines
Follow Conventional Commits (`feat:`, `fix:`, `chore:`) as shown in `git log`. Keep commits scope-focused and include migration or schema notes in the body when relevant. Each PR should outline the change, list testing performed, reference related issues, and attach screenshots for UI updates. Ensure CI-critical commands (`pytest`, `npm run lint`) pass before requesting review.

## Environment & Configuration
Copy `.env.example` to `.env` in `backend/` and `.env.local.example` to `.env.local` in `frontend/`; never commit secrets. Rotate keys referenced by `backend/firebase-service-account.json` through your secret manager and load them via environment variables. Document any new required settings in `DEPLOYMENT.md` and surface defaults in the example env files.
