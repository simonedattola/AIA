# AGENTS.md

## Cursor Cloud specific instructions

### Email (Resend)

- Delivery is via Resend in `backend/app/mailer.py`. Without `RESEND_API_KEY`, `send_email` no-ops and still returns success paths for forms/portal (data is saved).
- Staff inbox defaults to `NOTIFY_EMAIL=legnano@aia-figc.it` (contatti, candidature, testimonianze, foto galleria, reply su comunicazioni).
- Member opt-in flags: `emailNotifyComunicazioni`, `emailNotifyMessages`, `emailNotifyEvents` (+ `emailNotifyEventLeadHours`). UI: Area associati → Profilo.
- Event invite on create + reminder scheduler: `event_reminders.py` / `event_reminders_scheduler.py` (must be running with the backend process).
- Set `PORTAL_FRONTEND_URL` in production so member emails link to the live portal, not localhost.
- See `docs/GO_LIVE.md` § Email and `backend/.env.example` for variable names.

### Standard commands

- Backend: see `README.md` / `backend/requirements.txt` (`uvicorn` from `backend/`).
- Frontend: `npm start` in `frontend/` (CRA).
- Tests: `cd backend && .venv/bin/python -m pytest`.
