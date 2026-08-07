## Cursor Cloud specific instructions

### Stack
- **MongoDB** (required) + **FastAPI backend** (`:8000`) + **React CRA frontend** (`:3000`).
- Deprecated Next.js portal in `area-riservata/` is unused — do not start it for normal work.
- Standard commands: see root `README.md`. Env template: `backend/.env.example`.

### Run notes
- Backend seed runs on startup and syncs admin password from `ADMIN_PASSWORD`.
- CORS must be an explicit origin list (never `*`) because credentials are enabled; default is localhost:3000.
- Weak/default `JWT_SECRET` logs a warning at startup — set a long secret for any shared environment.
- Public GET endpoints do not write to Mongo (category/designation enrichment is in-memory only).
- Uploads: images max 8MB; attachments 10MB (videos 50MB); SVG uploads are rejected.
- Login and public forms are rate-limited in-memory per IP (429 when exceeded).

### Tests
- Unit tests (no server): `cd backend && pytest tests/test_query_utils.py tests/test_member_public.py tests/test_mailer_escape.py tests/test_*.py -q -k "not aia_legnano and not iter2"`
- Integration tests need Mongo + backend up and `REACT_APP_BACKEND_URL=http://localhost:8000`.
