# Contributing

Thanks for helping with AIA Legnano. This guide covers local setup, checks, and pull requests.

## Prerequisites

- Node.js ≥ 18 and npm (or yarn)
- Python ≥ 3.10
- MongoDB (local or remote URI)

## Local setup

Follow the root [`README.md`](../README.md) and [`DEPLOYMENT.md`](DEPLOYMENT.md) (development section).

```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --host 0.0.0.0 --port 8000

# Frontend (other terminal)
cd frontend && npm install --legacy-peer-deps && npm start
```

Copy env from examples when available (`backend/.env.example` → `backend/.env`). Never commit `.env` files or secrets.

## Branching & PRs

1. Branch from `main` with a descriptive name.
2. Keep PRs focused (one concern per PR when practical).
3. Describe *what* and *why* in the PR body; link issues if any.
4. Do not commit `backend/uploads/`, `backups/`, or build artifacts.

## Tests & quality

### Backend

```bash
cd backend
source .venv/bin/activate
pytest tests/ -q
# Prefer excluding heavy integration when iterating:
# pytest tests/ -m "not integration" -q
```

Optional: `flake8` / `black` on touched files when those tools are in CI.

### Frontend

```bash
cd frontend
npm run build
# npm test -- --watchAll=false   # when Jest suite is present
```

## Docs map

| Doc | Topic |
|-----|--------|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | System design |
| [`DEPLOYMENT.md`](DEPLOYMENT.md) | Dev / staging / production |
| [`BACKUP.md`](BACKUP.md) | Mongo + uploads backup (when merged) |

## Code notes

- Prefer real schema field names already used in Mongo (e.g. `memberId`, `matchDate`) over invented placeholders.
- Uploads go through `app.storage` so local and S3/R2 stay interchangeable.
- Portal lives in the main React app on port 3000; do not revive the deprecated Next app unless explicitly requested.
