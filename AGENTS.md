## Cursor Cloud specific instructions

### Stack
- **MongoDB** (required) + **FastAPI backend** (`:8000`) + **React CRA frontend** (`:3000`).
- Deprecated Next.js portal in `area-riservata/` is unused — do not start it for normal work.
- Standard commands: see root `README.md`. Env template: `backend/.env.example`.

### Route layout
- Admin API: `backend/app/routes/admin/` (domain modules, aggregated in `__init__.py`).
- Portal API: `backend/app/routes/portal/` (same pattern).
- Public API: `backend/app/routes/public.py`.

### Run notes
- Backend seed runs on startup and syncs admin password from `ADMIN_PASSWORD`.
- Startup also ensures Mongo indexes (`app/indexes.py`) and security headers middleware.
- Health: `GET /api/health` (pings Mongo; 503 if DB down).
- CORS must be an explicit origin list (never `*`) because credentials are enabled; default is localhost:3000.
- Weak/default `JWT_SECRET` logs a warning at startup — set a long secret for any shared environment.
- Public GET endpoints do not write to Mongo (category/designation enrichment is in-memory only).
- Uploads: images max 8MB; attachments 10MB (videos 50MB); SVG uploads are rejected.
- Login and public forms are rate-limited in-memory per IP (429 when exceeded).
- Portal password change requires ≥8 chars with letters+numbers (`validate_portal_password`).

### Tests
- Unit (no server): `cd backend && pytest -q -m "not integration"`
- Integration needs Mongo + backend up and `REACT_APP_BACKEND_URL=http://localhost:8000`.
