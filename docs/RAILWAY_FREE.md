# Railway Free ($1/mese) — deploy che fallisce

Sul piano **Free** Railway dà ~**$1 di credito/mese**. Dopo la prova, i deploy falliscono quasi sempre per uno di questi motivi.

## Fix #1 (il più comune) — Serverless “fantasma” (UI ON ma deploy rifiuta)

Errore tipico:

> `Free plan deployments must be serverless. Please go to your service settings and turn on the serverless flag.`

Anche se il toggle è già **ON**, dopo la scadenza della trial Railway a volte **non salva** il flag sul servizio. Fai esattamente questa sequenza:

### A — Resync del flag (funziona nella maggior parte dei casi)

1. Servizio → **Settings → Deploy → Serverless**
2. Metti Serverless su **OFF** e salva (se la UI lo permette)
3. Prova un deploy (può fallire: ok)
4. Rimetti Serverless su **ON** e salva
5. **Non** cliccare Redeploy sul deploy rosso vecchio
6. `Ctrl/Cmd + K` → cerca **Deploy latest commit** → invio  
   (oppure: Settings → Source → **Disconnect** / **Reconnect** repo, poi Deploy)

### B — Se A fallisce ancora: servizio nuovo (pulito)

Il vecchio servizio può restare “incastrato”. Crea un servizio nuovo:

1. Stesso progetto Railway → **New → GitHub Repo** → `simonedattola/AIA`
2. **Root Directory:** `backend`
3. Builder: Dockerfile
4. **Subito** Settings → Deploy → **Serverless ON**
5. Copia le variabili d’ambiente dal servizio vecchio
6. Deploy → Generate domain
7. Aggiorna `frontend/vercel.json` con il **nuovo** URL `*.up.railway.app`
8. (Opzionale) elimina il servizio vecchio rotto

### C — Peak hours Free

Sul Free i deploy possono essere bloccati in fascia di punta (spesso ~08–20 ora della regione del servizio). Riprova più tardi la notte se A/B falliscono senza log di build.

## Fix #2 — Root Directory e Dockerfile

Il servizio deve buildare dalla cartella **`backend`**:

| Setting | Valore |
|---------|--------|
| Root Directory | `backend` |
| Builder | Dockerfile |
| Dockerfile path | `Dockerfile` (relativo a `backend`) |
| Healthcheck path | `/api/health` |
| Healthcheck timeout | ≥ 120 s (cold start Serverless) |

Config di riferimento: `backend/railway.toml`.

## Fix #3 — Variabili obbligatorie

Senza `MONGO_URL` valido il container parte ma il **healthcheck fallisce** (503) e Railway marca il deploy come failed.

Minimo:

- `MONGO_URL` = Atlas `mongodb+srv://…`
- `DB_NAME` = `aia_legnano`
- `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`
- `CORS_ORIGINS` = `https://www.aia-legnano.it,https://aia-legnano.it,https://aia-virid.vercel.app`
- `PORTAL_FRONTEND_URL` = `https://www.aia-legnano.it`
- `DESIGNATIONS_AUTO_SYNC` = `true`

## Fix #4 — credito e sleep

Con Serverless il servizio **dorme** dopo ~10 min senza traffico **in uscita** (Mongo/heartbeat contano).

- `$1/mese` **non basta** per tenerlo sempre acceso.
- Per la sync designazioni: cron gratis ogni **10 min** su  
  `https://TUO-SERVIZIO.up.railway.app/api/health`  
  (cron-job.org / UptimeRobot). Il watchdog avvia la sync se scadute le 6h.
- Consigliato su Free: `EVENT_REMINDERS_ENABLED=false` (il loop ogni 5 min tiene sveglio il servizio e brucia il credito).

## Dopo un deploy riuscito

1. Genera dominio pubblico (Settings → Networking → Generate domain).
2. Aggiorna `frontend/vercel.json`: sostituisci  
   `https://aia-production-00a9.up.railway.app`  
   con il nuovo host Railway.
3. Verifica:

```bash
curl -sS "https://NUOVO-HOST.up.railway.app/api/health"
curl -sS "https://www.aia-legnano.it/api/health"
```

## Se il credito finisce a metà mese

Il servizio torna `Application not found` / sospeso fino al rinnovo del credito o upgrade **Hobby (~$5/mese)** (sempre acceso, senza peak hours).

Vedi anche [`FREE_HOSTING.md`](FREE_HOSTING.md) per Render Free come alternativa.
