# Railway Free ($1/mese) — deploy che fallisce

Sul piano **Free** Railway dà ~**$1 di credito/mese**. Dopo la prova, i deploy falliscono quasi sempre per uno di questi motivi.

## Fix #1 (il più comune) — abilita Serverless

Errore tipico nei log:

> `Free plan deployments must be serverless. Please go to your service settings and turn on the serverless flag.`

1. Railway → progetto → servizio **backend**
2. **Settings → Deploy → Serverless** → **Enable Serverless** (ON)
3. Non usare “Redeploy” su un deploy vecchio (tiene lo snapshot senza flag).
4. Apri la command palette (`Ctrl/Cmd+K`) → **Deploy latest commit**

Aspetta il build. Se fallisce ancora, prova **fuori dalle peak hours** Free (di solito 08:00–20:00 fuso della regione del servizio) oppure ricrea il servizio con Serverless già ON.

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
