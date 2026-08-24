# AGENTS.md

## Cursor Cloud specific instructions

### Email (Resend)

- Delivery is via Resend in `backend/app/mailer.py`. Without `RESEND_API_KEY`, `send_email` no-ops and still returns success paths for forms/portal (data is saved).
- Staff inbox defaults to `NOTIFY_EMAIL=legnano@aia-figc.it` (contatti, candidature, testimonianze, foto galleria, reply su comunicazioni).
- Member opt-in flags: `emailNotifyComunicazioni`, `emailNotifyMessages`, `emailNotifyEvents` (+ `emailNotifyEventLeadHours`). UI: Area associati → Profilo.
- Event invite on create + reminder scheduler: `event_reminders.py` / `event_reminders_scheduler.py` (must be running with the backend process).
- Set `PORTAL_FRONTEND_URL` in production so member emails link to the live portal, not localhost.
- See `docs/GO_LIVE.md` § Email and `backend/.env.example` for variable names.

### Produzione / dominio www.aia-legnano.it

- Guida cutover: `docs/CUSTOM_DOMAIN.md`
- Frontend Vercel proxy `/api` → Railway (`frontend/vercel.json`). In Production Vercel lascia `REACT_APP_BACKEND_URL` **vuoto**.
- Backend Railway attuale: `https://aia-production-00a9.up.railway.app`
- Dopo DNS: `PORTAL_FRONTEND_URL=https://www.aia-legnano.it`, `CORS_ORIGINS` con dominio reale, `PUBLIC_API_URL=https://api.aia-legnano.it` (opzionale)
- Smoke test: `./scripts/verify_go_live.sh https://www.aia-legnano.it`

### Standard commands

- Backend: see `README.md` / `backend/requirements.txt` (`uvicorn` from `backend/`).
- Frontend: `npm start` in `frontend/` (CRA).
- Tests: `cd backend && .venv/bin/python -m pytest`.
