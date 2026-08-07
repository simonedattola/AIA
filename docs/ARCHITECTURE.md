# Architecture Overview

AIA Legnano is a monorepo: **React (CRA)** public site + admin + member portal, **FastAPI** API, **MongoDB** persistence.

## System diagram

```
┌─────────────────────────────────────┐
│  Frontend (React + Tailwind)        │
│  - Public site                      │
│  - Admin panel                      │
│  - Area riservata (associati)       │
│  Deploy: Vercel (production)        │
└──────────────┬──────────────────────┘
               │ HTTPS (REACT_APP_BACKEND_URL)
               ▼
┌─────────────────────────────────────┐
│  Backend (FastAPI / uvicorn)        │
│  - REST API + JWT                   │
│  - Public / admin / portal routers  │
│  - Schedulers (designazioni, …)     │
│  Deploy: custom host (not Vercel)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  MongoDB (aia_legnano)              │
│  Members, articles, events,         │
│  designations, gallery, portal…     │
└─────────────────────────────────────┘
               │
               ▼ (optional production)
┌─────────────────────────────────────┐
│  Object storage (S3 / R2) + CDN     │
│  Uploads; local UPLOAD_DIR in dev   │
└─────────────────────────────────────┘
```

## Key components

### Backend routes

| Prefix | Role |
|--------|------|
| `/api/` | Health / root |
| `/api/public/*` | Public content (articles, events, members, designations, forms) |
| `/api/admin/*` | Admin CRUD (JWT admin) |
| `/api/portal/*` | Member portal (JWT member / meccanografico login) |
| `/api/uploads/*` | Uploaded media (local static or S3 proxy/CDN) |

Entrypoint: `backend/server.py`. Domain logic under `backend/app/` (`routes/`, scrapers, seed, schedulers).

### Frontend surfaces

| Path | Role |
|------|------|
| `/` | Home (news, designazioni, chi siamo, …) |
| `/admin/*` | Admin panel (articles, events, members, settings, sync) |
| `/area-riservata/login` | Portal login (integrated on port 3000) |
| Public content routes | Articles, events, gallery, forms, etc. |

Legacy Next.js app in `area-riservata/` is **deprecated** (see `area-riservata/DEPRECATED.md`).

### Auth

- **Admin:** email + password → JWT (`Authorization: Bearer`).
- **Portal:** codice meccanografico + password → member JWT.
- Secrets via env (`JWT_SECRET`, `ADMIN_*`); never commit real credentials.

## Data flows

1. **Article publish**  
   Admin creates/edits article → `POST/PUT /api/admin/articles` → Mongo `articles` → public site reads `/api/public/...`.

2. **Designations sync**  
   Scheduler (or `POST /api/admin/designations/sync-aia`) crawls AIA FIGC → parse → upsert `members` + `designations` (filtered to Legnano by config).

3. **Member portal**  
   Login with meccanografico → JWT → `/api/portal/*` (presenze, messaggi, gallery upload, profile photo).

4. **Uploads**  
   Admin/portal upload → `app.storage` writes to `UPLOAD_DIR` or S3 → clients resolve `/api/uploads/{name}` (or CDN when `S3_PUBLIC_BASE_URL` is set).

5. **Seed on startup**  
   Idempotent seed + optional index ensure / portal password backfill (see `on_startup` in `server.py`).

## Related

- [`DEPLOYMENT.md`](DEPLOYMENT.md) — env and hosting
- [`BACKUP.md`](BACKUP.md) — backup / DR (Phase 6+)
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to develop and open PRs
