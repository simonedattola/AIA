# Testing — AIA Legnano

## Backend (`backend/`)

### Markers (`pytest.ini`)

| Marker | Meaning |
|--------|---------|
| `unit` | Pure unit tests (no live HTTP API). Default for CI. |
| `integration` | Needs a running API (`REACT_APP_BACKEND_URL`) and/or seeded MongoDB |

Integration modules (excluded from CI with `-m "not integration"`):

- `tests/test_aia_legnano.py` — full public/admin HTTP suite against a live backend
- `tests/test_iter2_blocks.py` — CMS blocks via live API
- `tests/test_member_profile.py` — ASGI + Mongo member profile

### Run locally

```bash
cd backend
python -m pip install -r requirements.txt

# Unit only (same as CI)
export MONGO_URL=mongodb://localhost:27017
export DB_NAME=aia_test
export JWT_SECRET=test-secret-key-for-ci-only-not-production
export ADMIN_EMAIL=test@example.com
export ADMIN_PASSWORD=test
export PYTHONPATH=$PWD
pytest tests/ -v -m "not integration"

# Integration (backend must be running + seeded)
export REACT_APP_BACKEND_URL=http://localhost:8000
export ADMIN_PASSWORD=<from backend/.env>
pytest tests/ -v -m integration
```

CI workflow: `.github/workflows/backend-test.yml` runs `pytest tests/ -v -m "not integration"`.

## Frontend (`frontend/`)

Uses **Jest via CRA/craco** (`react-scripts` Jest 27) + Testing Library.

```bash
cd frontend
npm ci --legacy-peer-deps
npm test                 # CI mode: --watchAll=false
npm run test:watch       # interactive watch
```

Critical component/unit tests live under `src/**/__tests__/` and `src/**/*.test.jsx`.
