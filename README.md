# AIA Legnano – Piattaforma web

Sito istituzionale e pannello admin per la Sezione AIA di Legnano (React + FastAPI + MongoDB).

## Requisiti

- **Node.js** ≥ 18 (con npm o yarn)
- **Python** ≥ 3.10
- **MongoDB** in esecuzione locale o remoto

## Configurazione

1. Copia le variabili d'ambiente del backend:

```bash
cp backend/.env.example backend/.env
```

Modifica `backend/.env` (almeno `MONGO_URL`, `DB_NAME`, `JWT_SECRET`, credenziali admin).

2. Frontend – crea `frontend/.env`:

```
REACT_APP_BACKEND_URL=http://localhost:8000
```

## Area riservata associati (integrata, porta 3000)

- URL: `http://localhost:3000/area-riservata/login`
- API: `http://localhost:8000/api/portal/*`
- Login: **codice meccanografico** + password (iniziale `nome.cognome`, es. `mario.rossi`)
- Admin: **Presenze** e **Notifiche portale** nel pannello `/admin`

La cartella `area-riservata/` (Next.js su 3001) è **deprecata** — vedi `area-riservata/DEPRECATED.md`.

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

### Sync automatico (ogni 12 ore)

Con il backend avviato, le designazioni degli arbitri **sezione Legnano** vengono importate automaticamente da AIA FIGC:

- **Prima esecuzione:** ~90 secondi dopo l’avvio (dopo il seed)
- **Poi:** ogni **12 ore** (configurabile)

Variabili in `backend/.env`:

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `DESIGNATIONS_AUTO_SYNC` | `true` | Abilita/disabilita il job |
| `DESIGNATIONS_SYNC_INTERVAL_HOURS` | `12` | Intervallo tra due sync |
| `DESIGNATIONS_SYNC_ON_STARTUP` | `true` | Sync anche all’avvio |
| `DESIGNATIONS_LEGNANO_GARE` | `3-270` | Codice sezione AIA Legnano |
| `DESIGNATIONS_FILTER_SECTION` | `Legnano` | Solo nominativi di quella sezione |

Per disattivare: `DESIGNATIONS_AUTO_SYNC=false`


## Backup & disaster recovery

See [`docs/BACKUP.md`](docs/BACKUP.md) for `mongodump` / `mongorestore`, uploads archives, cron examples, and production (Atlas + object storage) guidance.

MongoDB indexes are ensured on API startup via `app.db_indexes.create_indexes()`.

## Test backend

```bash
cd backend
REACT_APP_BACKEND_URL=http://localhost:8000 pytest tests/ -v
```

(I test di integrazione richiedono il server in esecuzione e MongoDB configurato.)

## Area riservata associati

- Nel menu pubblico: voce **Area riservata** (o `/area/riservata`)
- Nel pannello admin: link **Area riservata** nella sidebar
- Portale: `http://localhost:3001` (con `docker compose up` include il servizio `area-riservata`)
- Login: **codice meccanografico** + password iniziale `nome.cognome` (es. Mario Rossi → codice assegnato / `mario.rossi`)
- In Admin → Associati imposta il codice meccanografico: all’aggiornamento viene creato/sincronizzato l’account portale

## Credenziali admin (seed)

- Email: valore di `ADMIN_EMAIL` in `.env` (default `admin@aia-legnano.it`)
- Password: valore di `ADMIN_PASSWORD` in `.env`
