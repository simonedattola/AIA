# Deployment Guide

How to run AIA Legnano in **development**, **staging**, and **production**.

## Environments overview

| Environment | Frontend | Backend | Database |
|-------------|----------|---------|----------|
| Development | CRA on `:3000` | uvicorn on `:8000` | Local Mongo / Compose |
| Staging | Docker image / stack | Docker image / stack | Managed or Compose Mongo |
| Production | Vercel (GitHub) | Custom host (Railway / Render / ECS) | MongoDB Atlas (recommended) |

---

## Development (local)

### Option A — Docker Compose

```bash
docker compose up
```

Services: Mongo (`27017`), API (`8000`), frontend (`3000`).  
Uploads persist in the `backend-uploads` volume (`UPLOAD_DIR=/app/backend/uploads`).

### Option B — Native processes

1. Start MongoDB (`mongod` or Atlas connection string in `backend/.env`).
2. Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

3. Frontend:

```bash
cd frontend
npm install --legacy-peer-deps   # or yarn
npm start
```

Required env (see `backend/.env` / root `.env`):

- `MONGO_URL`, `DB_NAME`
- `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`
- `CORS_ORIGINS`, `PUBLIC_API_URL` / `REACT_APP_BACKEND_URL`

---

## Staging (Docker)

Build images:

```bash
docker build -t aia-frontend:latest ./frontend
docker build -t aia-backend:latest ./backend
```

Deploy with Compose on a staging host (or Swarm when you add a stack file):

```bash
# Compose (typical for a single staging VM)
docker compose -f docker-compose.yml up -d --build

# Swarm (when docker-stack.yml is maintained)
# docker stack deploy -c docker-stack.yml aia-staging
```

Point staging DNS at the host; set env to non-production secrets and a staging Mongo URI.

---

## Production

### Frontend — Vercel

- Deployed from the GitHub repo (Vercel project linked to `frontend/` or monorepo root with Root Directory = `frontend`).
- Env: `REACT_APP_BACKEND_URL` = public API origin (no trailing slash).
- Example preview domain: `https://aia-legnano.vercel.app` (replace with the real Vercel / custom domain once configured).

Build command (CRA): `npm run build` (or `yarn build`). Output: `build/`.

### Backend — custom infrastructure

**Not** hosted on Vercel for this project. Prefer:

| Option | When |
|--------|------|
| **A** Railway / Render / Fly.io / similar | Fast bootstrap, single service |
| **B** AWS ECS (or EC2) + Atlas | Scale, VPC, tighter ops control |

Expose HTTPS (reverse proxy / platform TLS). Process example:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 2
```

Or run the `backend/Dockerfile` image behind a load balancer.

#### Required production env vars

| Variable | Purpose |
|----------|---------|
| `MONGO_URL` | Production MongoDB (Atlas recommended) |
| `DB_NAME` | Usually `aia_legnano` |
| `JWT_SECRET` | Strong secret (GitHub Secrets / vault) |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Initial admin (from vault; rotate after seed) |
| `PUBLIC_API_URL` | Public backend origin (e.g. `https://api.example.com`) |
| `CORS_ORIGINS` | Frontend origin(s), comma-separated |
| `REACT_APP_BACKEND_URL` | Same API URL for the frontend build |

#### Uploads (production)

Prefer object storage instead of the container filesystem:

```bash
STORAGE_BACKEND=s3
S3_BUCKET=...
S3_ENDPOINT_URL=...          # R2 / MinIO; omit for AWS
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_PUBLIC_BASE_URL=https://cdn.example.com
```

See [`BACKUP.md`](BACKUP.md) for dump/restore and bucket migration notes.

#### Health check

```bash
curl -sS "$PUBLIC_API_URL/api/" 
# Prefer /api/health when monitoring PR is merged
```

---

## Backend deployment URL

Document the live API base URL here once provisioned (Task 7.2):

| Slot | URL |
|------|-----|
| Production API | _TBD — set after Railway/Render/ECS go-live_ |
| Staging API | _TBD_ |
| Local API | `http://localhost:8000` |

Update README **Production URLs** when these are known.

---

## Related docs

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — system diagram and data flows
- [`BACKUP.md`](BACKUP.md) — Mongo + uploads backup / DR (when present on the branch)
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — local workflow and PRs
