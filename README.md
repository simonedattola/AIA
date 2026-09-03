# AIA Legnano – Piattaforma web

Sito istituzionale e pannello admin per la Sezione AIA di Legnano (React + FastAPI + MongoDB).

## Versione unica (importante)

C’è **una sola versione del sito**: il branch **`main`**.

| Cosa | Dove |
|------|------|
| Codice ufficiale | `main` |
| Sito in locale | `http://localhost:3000` |
| API in locale | `http://localhost:8000` |
| Backup pre go-live | branch `backup/pre-go-live` (solo ripristino) |

Non usare altre branch feature per sviluppare o per aprire Chrome: creano confusioni (loghi mancanti, layout diversi).

```bash
git checkout main
git pull origin main
```

## Requisiti

- **Node.js** ≥ 18 (con npm o yarn)
- **Python** ≥ 3.10
- **MongoDB** in esecuzione locale o remoto

## Configurazione

### Secret e variabili d'ambiente

**Non committare mai file `.env` con password o JWT reali.** I template nel repo usano solo placeholder.

1. **Sviluppo locale (uvicorn senza Docker)** — copia il template backend:

```bash
cp backend/.env.example backend/.env
```

Modifica `backend/.env` e imposta almeno:

| Variabile | Note |
|-----------|------|
| `MONGO_URL` | es. `mongodb://localhost:27017` |
| `DB_NAME` | es. `aia_legnano` |
| `JWT_SECRET` | stringa casuale lunga (≥32 caratteri). Es: `openssl rand -base64 48` |
| `ADMIN_EMAIL` | email admin seed |
| `ADMIN_PASSWORD` | password forte (obbligatoria; niente default in codice) |

2. **Docker Compose** — usa il template in root:

```bash
cp .env.example .env
# genera secret, poi:
docker compose up --build
```

Compose legge `.env` in root e **richiede** `JWT_SECRET`, `ADMIN_EMAIL` e `ADMIN_PASSWORD` (nessun valore hardcoded in `docker-compose.yml`).

3. Frontend — crea `frontend/.env` (non secret). Per sviluppo locale con proxy CRA preferisci URL vuoto:

```
REACT_APP_BACKEND_URL=
```

(alternativa diretta: `REACT_APP_BACKEND_URL=http://localhost:8000`)

Per i test di integrazione backend, esporta le stesse credenziali admin (`ADMIN_PASSWORD`, opzionalmente `ADMIN_EMAIL`) prima di `pytest`.

### GitHub Actions secrets (CI/CD)

I secret di pipeline **non** vanno nel codice: vanno creati in GitHub
(**Settings → Secrets and variables → Actions**).

Elenco completo, generazione, checklist e procedura di rotazione:
[`.github/SECRETS.md`](.github/SECRETS.md).

## Area riservata associati (integrata, porta 3000)

- URL: `http://localhost:3000/area-riservata/login`
- API: `http://localhost:8000/api/portal/*`
- Login: **codice meccanografico** + password (iniziale `nome.cognome`, es. `mario.rossi`)
- Admin: **Presenze** e **Notifiche portale** nel pannello `/admin`

## Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

All'avvio viene eseguito il seed idempotente (dati demo + utente admin).

API: `http://localhost:8000/api/`

### Health & Monitoring

- **Health endpoint:** `GET /api/health` — returns service status (`database`, `cache`) and UTC timestamp
- **Logs:** Structured JSON logs to stdout (aggregate with ELK / Datadog / CloudWatch). Set `LOG_LEVEL` (default `INFO`).
- **Metrics:** Prometheus-style gauges at `GET /metrics` (`aia_api_up`, `aia_api_uptime_seconds`, `aia_api_database_up`)

Example health payload:

```json
{
  "status": "healthy",
  "timestamp": "2026-08-07T20:00:00Z",
  "services": {
    "database": "connected",
    "cache": "N/A"
  }
}
```


## Frontend

```bash
cd frontend
yarn install   # oppure: npm install
yarn start     # oppure: npm start
```

App: `http://localhost:3000`

## Sincronizzazione designazioni (AIA FIGC)

Le designazioni possono essere importate automaticamente dal portale ufficiale:

- Home designazioni: https://www.aia-figc.it/designazioni/ — tutti gli hub regionali/nazionali vengono scoperti da questa pagina (escluso solo `/designazioni/can/` Serie A).
- Lombardia: tutte le sezioni provinciali (inclusa Legnano), non solo `gare=3-270`.
- Altri hub (C.A.N., altre regioni): crawl automatico con `DESIGNATIONS_CRAWL_ALL_HUBS=true` (default); in DB restano solo le righe con sezione **Legnano** (`DESIGNATIONS_FILTER_SECTION`).

**Da admin:** Designazioni → pulsante **Sync AIA FIGC** (richiede rete verso `aia-figc.it`).

**Da API:** `POST /api/admin/designations/sync-aia` (JWT admin) con body opzionale:

```json
{
  "sectionGare": "3-270",
  "filterSection": "Legnano",
  "replaceExisting": true
}
```

### Sync automatico (ogni 6 ore)

Con il backend avviato, le designazioni degli arbitri **sezione Legnano** vengono importate automaticamente da AIA FIGC:

- **Prima esecuzione:** ~90 secondi dopo l’avvio se l’ultimo sync è in ritardo (catch-up)
- **Poi:** ogni **6 ore** (configurabile)
- **Manuale (admin):** avvio in background; lo stato si aggiorna su `GET /api/admin/designations/sync-status` (il crawl AIA dura 1–3 minuti e non deve restare appeso al POST)

Variabili in `backend/.env`:

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `DESIGNATIONS_AUTO_SYNC` | `true` | Abilita/disabilita il job |
| `DESIGNATIONS_SYNC_INTERVAL_HOURS` | `6` | Intervallo tra due sync |
| `DESIGNATIONS_LEGNANO_GARE` | `3-270` | Codice sezione AIA Legnano |
| `DESIGNATIONS_FILTER_SECTION` | `Legnano` | Solo nominativi di quella sezione |

Per disattivare: `DESIGNATIONS_AUTO_SYNC=false`

## API documentation (Swagger)

With the backend running:

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Swagger UI (try endpoints, Authorize with JWT) |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/openapi.json | OpenAPI schema |

Admin: `POST /api/admin/login` → paste token in **Authorize**. Portal: `POST /api/portal/login`.

## Documentation

| Doc | Description |
|-----|-------------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System diagram and data flows |
| [`docs/CUSTOM_DOMAIN.md`](docs/CUSTOM_DOMAIN.md) | DNS Aruba + Vercel + Railway (www.aia-legnano.it) |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Development, staging, production |
| [`docs/BACKUP.md`](docs/BACKUP.md) | Mongo + uploads backup / DR |
| [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) | Local workflow and PR guidelines |
| [`docs/VERIFICATION.md`](docs/VERIFICATION.md) | Phase 9 production-readiness checklist |
| [`.github/SECRETS.md`](.github/SECRETS.md) | GitHub Actions secrets |
| [`.github/CI.md`](.github/CI.md) | CI workflows and branch protection |

## Production URLs

| Surface | URL |
|---------|-----|
| Frontend (produzione) | `https://www.aia-legnano.it` |
| Frontend (preview Vercel) | `https://aia-virid.vercel.app` |
| Backend API (Railway) | `https://aia-production-00a9.up.railway.app` |
| API custom (opzionale) | `https://api.aia-legnano.it` |
| Local frontend | `http://localhost:3000` |
| Local API | `http://localhost:8000` |

Cutover DNS: [`docs/CUSTOM_DOMAIN.md`](docs/CUSTOM_DOMAIN.md)

## Testing

See [`backend/TESTING.md`](backend/TESTING.md) for pytest markers (unit vs integration) and frontend Jest commands.

```bash
# Backend unit tests (CI-equivalent)
cd backend && pytest tests/ -m "not integration" -q

# Frontend
cd frontend && npm test -- --watchAll=false
```

Integration tests require a running API + `ADMIN_PASSWORD` and are excluded from CI.

## Area riservata associati

- Nel menu pubblico: voce **Area riservata** (o `/area/riservata`)
- Nel pannello admin: link **Area riservata** nella sidebar
- Portale integrato: `http://localhost:3000/area-riservata/login` (API `/api/portal/*`)
- Login: **codice meccanografico** + password iniziale `nome.cognome`

## Credenziali admin (seed)

- Email: `ADMIN_EMAIL` (default produzione: `legnano@aia-figc.it`)
- Password iniziale: `ADMIN_PASSWORD` in env (solo alla creazione; i reset via email restano validi)
- Rotazione da env: imposta `ADMIN_PASSWORD_FORCE_SYNC=true` per un deploy, poi rimuovi
- **Password dimenticata:** `/amministrazione/password-dimenticata` → email con link (richiede `RESEND_API_KEY`)

## Status & Roadmap

### v1.0 (Current — integrated on verification branch)

- [x] Public site + admin panel
- [x] Member portal
- [x] Designations sync (AIA FIGC)
- [x] Mobile-first responsive UI (PR #6)
- [x] Security hardening (PR #5 / #7)
- [x] CI workflows + unit tests (PR #8 / #10)
- [x] OpenAPI / Swagger (PR #9)
- [x] Health + JSON logs + metrics (PR #11)
- [x] DB indexes + backup docs + S3 adapter (PR #12)
- [x] Architecture / deployment docs (PR #13)

### v1.1 (Ops follow-ups)

- [ ] Merge PRs #5–#13 to `main` and enable branch protection (`verify`)
- [ ] Configure GitHub Actions secrets in the repo UI
- [ ] Rotate `JWT_SECRET` / `ADMIN_PASSWORD` (history still contains old defaults)
- [ ] E2E testing (Playwright)
- [ ] Scheduled backup automation in production
- [ ] Vercel re-deploy + backend URL go-live

---

## Contributing

See [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) for local development, testing, and PR guidelines.

---

## License

© 2026 AIA Legnano. All rights reserved.
