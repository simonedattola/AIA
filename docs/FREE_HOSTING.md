# Hosting gratuito (alternativa a Railway)

Stack consigliato **a costo zero**:

| Pezzo | Dove | Piano |
|-------|------|-------|
| Frontend | **Vercel** (già attivo) | Hobby free |
| Backend FastAPI | **Render** Web Service | Free |
| Database | **MongoDB Atlas** (già attivo) | M0 free |
| Keep-alive + sync | **cron-job.org** (o simile) | Free |

Railway non è più gratis dopo la prova: il sito “vuoto” dipende dal backend spento (`Application not found`), non dal frontend.

## Limiti del piano Free Render

- Dopo ~**15 minuti** senza traffico il servizio va in sleep.
- Il risveglio richiede ~**30–60 secondi** (prima richiesta lenta).
- **750 ore/mese** di istanza: con sleep i minuti idle non contano; con keep-alive ogni 10 min resti entro il limite tipico di un solo servizio.
- Niente disco persistente: usa **GridFS / Atlas** (già `STORAGE_BACKEND=auto` su `mongodb+srv`).

Lo scheduler designazioni in-process non gira mentre il servizio dorme. Il watchdog su `GET /api/health` + un cron esterno risolvono: ogni ping riaccende il servizio e, se scadute le 6h, avvia la sync.

---

## Passo 1 — Deploy backend su Render

1. Account su [render.com](https://render.com) (carta non obbligatoria per Free).
2. **New → Blueprint** (oppure **Web Service**) e collega il repo `simonedattola/AIA`.
3. Se usi Blueprint: seleziona `render.yaml` (root del repo).
4. Se crei Web Service a mano:
   - **Root Directory:** `backend`
   - **Runtime:** Docker (`Dockerfile`)
   - **Instance type:** Free
   - **Health Check Path:** `/api/health`
5. Variabili (Dashboard → Environment) — **stesse di Railway / Atlas**:

| Variabile | Note |
|-----------|------|
| `MONGO_URL` | Connection string Atlas (`mongodb+srv://…`) |
| `DB_NAME` | es. `aia_legnano` |
| `JWT_SECRET` | stesso di prima (sessioni admin) |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | admin |
| `CORS_ORIGINS` | `https://www.aia-legnano.it,https://aia-legnano.it,https://aia-virid.vercel.app` |
| `PORTAL_FRONTEND_URL` | `https://www.aia-legnano.it` |
| `DESIGNATIONS_AUTO_SYNC` | `true` |
| `DESIGNATIONS_SYNC_INTERVAL_HOURS` | `6` |
| `RESEND_API_KEY` / email | se usi notifiche |
| `INSTAGRAM_SESSION_ID` | opzionale |

6. Deploy → copia l’URL pubblico, es. `https://aia-backend-xxxx.onrender.com`.

Verifica:

```bash
curl -sS "https://TUO-SERVIZIO.onrender.com/api/health"
# aspetta fino a ~1 min al primo cold start
```

Deve rispondere `status: healthy` e `database: connected`.

---

## Passo 2 — Punta Vercel al nuovo backend

In `frontend/vercel.json` sostituisci **tutte** le occorrenze di:

`https://aia-production-00a9.up.railway.app`

con:

`https://TUO-SERVIZIO.onrender.com`

Poi merge/deploy Vercel (o Redeploy da dashboard).

Smoke test:

```bash
./scripts/verify_go_live.sh https://www.aia-legnano.it
# oppure:
curl -sS "https://www.aia-legnano.it/api/health"
```

---

## Passo 3 — Keep-alive gratuito (obbligatorio per Free)

Su [cron-job.org](https://cron-job.org) (o EasyCron / UptimeRobot):

- **URL:** `https://TUO-SERVIZIO.onrender.com/api/health`  
  (oppure `https://www.aia-legnano.it/api/health` dopo il passo 2)
- **Intervallo:** ogni **10 minuti**
- **Metodo:** GET

Effetti:

1. Il servizio non resta in sleep troppo a lungo.
2. Il watchdog designazioni può avviare la sync se sono passate 6 ore.

---

## Alternative (se Render non basta)

| Opzione | Costo | Note |
|---------|-------|------|
| Render Free + cron | €0 | Consigliata; cold start possibile |
| Railway Hobby | ~$5/mese | Sempre acceso, meno attrito |
| Fly.io | ~$2/mese | Niente free per nuovi account |
| Oracle Cloud Always Free (VM) | €0 | Sempre acceso; più lavoro ops |

**Non** spostare Mongo su Render Postgres free: scade e non è il DB del progetto. Resta su **Atlas M0**.

---

## Checklist post-migrazione

- [ ] `GET …/api/health` → healthy + DB connected
- [ ] Home `www.aia-legnano.it` mostra news / designazioni
- [ ] Login admin funziona
- [ ] Sync designazioni manuale OK
- [ ] Cron ogni 10 min attivo
- [ ] `DESIGNATIONS_AUTO_SYNC=true` su Render
- [ ] Aggiornato `docs/DEPLOYMENT.md` con il nuovo URL API
