# CI / merge gate — AIA Legnano

## Workflows

| Workflow | File | Purpose |
|----------|------|---------|
| Backend Test & Lint | [`.github/workflows/backend-test.yml`](workflows/backend-test.yml) | flake8 (critical), black `--check`, mypy (soft), pytest `-m "not integration"` + Mongo 7 service |
| Frontend Test & Build | [`.github/workflows/frontend-test.yml`](workflows/frontend-test.yml) | ESLint + production `craco`/`react-scripts` build |
| PR Checks | [`.github/workflows/pr-checks.yml`](workflows/pr-checks.yml) | Calls both workflows; job **`verify`** fails unless both succeed |

## Local commands (same as CI)

```bash
# Backend
cd backend
python -m pip install -r requirements.txt
flake8 app tests --count --select=E9,F63,F7,F82 --show-source --statistics
black --check app tests
pytest tests/ -v --tb=short -m "not integration"

# Frontend
cd frontend
npm ci --legacy-peer-deps
npm run lint
CI=true npm run build
```

## Branch protection (required for “cannot merge until CI passes”)

GitHub Actions alone does not block merges. A repo admin must:

1. Open **Settings → Branches → Add/Edit branch protection rule** for `main`.
2. Enable **Require status checks to pass before merging**.
3. Select the status check named **`verify`** (from workflow **PR Checks**). Optionally also require the individual backend/frontend jobs.
4. Enable **Require branches to be up to date before merging** (recommended).
5. Save.

Until this is configured, PRs can still be merged with failing CI.

## Secrets

CI unit jobs use ephemeral non-production env vars inline (JWT/admin for pytest only).
Deploy secrets are documented in [SECRETS.md](SECRETS.md) (if present on your branch).

## Test docs

See [`backend/TESTING.md`](../backend/TESTING.md) for unit vs integration markers and frontend Jest.
