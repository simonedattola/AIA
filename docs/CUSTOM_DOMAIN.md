# Dominio produzione: www.aia-legnano.it

Guida per sostituire il sito WordPress su Aruba con la nuova piattaforma (Vercel + backend + Atlas).

Per backend **gratuito** (Render invece di Railway): vedi [`FREE_HOSTING.md`](FREE_HOSTING.md).

## Architettura live

| Componente | URL produzione | Hosting |
|------------|----------------|---------|
| Sito pubblico + admin + portale | `https://www.aia-legnano.it` | **Vercel** |
| Redirect apex | `https://aia-legnano.it` → `www` | **Vercel** |
| API backend | URL Render `https://….onrender.com` (poi opz. `https://api.aia-legnano.it`) | **Render** (ex Railway) |
| Database | MongoDB Atlas | **Atlas** |
| Email invio | `noreply@aia-legnano.it` | **Resend** |
| Email ricezione sezione | `legnano@aia-figc.it` | **Aruba** (MX invariati) |

Il frontend su Vercel **inoltra** `/api/*` al backend Railway (`frontend/vercel.json`), così browser e associati usano lo stesso dominio del sito.

---

## Passo 1 — Vercel (frontend)

1. Progetto Vercel collegato al repo GitHub, **Root Directory** = `frontend`.
2. **Settings → Domains** → aggiungi:
   - `www.aia-legnano.it`
   - `aia-legnano.it` (redirect a `www`, consigliato)
3. **Settings → Environment Variables** (Production):
   - `REACT_APP_BACKEND_URL` = **vuoto** (non impostare, oppure stringa vuota)  
     → il build usa `/api` same-origin e il proxy in `vercel.json`.
4. Redeploy Production dopo merge di questa configurazione.

Verifica Vercel (prima del DNS):

```bash
curl -sS "https://<preview-o-production-vercel>.vercel.app/api/health"
```

Deve rispondere JSON `healthy`, non HTML del SPA.

---

## Passo 2 — Backend (Render Free)

Railway non è più sul piano gratuito: usa **Render Free** — procedura completa in [`FREE_HOSTING.md`](FREE_HOSTING.md) (`render.yaml`).

**Variabili Production** (stesse chiavi di prima):

| Variabile | Valore |
|-----------|--------|
| `MONGO_URL` | URI Atlas `mongodb+srv://…` |
| `DB_NAME` | `aia_legnano` |
| `JWT_SECRET` | segreto forte (≥32 byte) |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | admin produzione |
| `PUBLIC_API_URL` | URL Render oppure `https://api.aia-legnano.it` dopo DNS |
| `PORTAL_FRONTEND_URL` | `https://www.aia-legnano.it` |
| `CORS_ORIGINS` | `https://www.aia-legnano.it,https://aia-legnano.it,https://aia-virid.vercel.app` |
| `DESIGNATIONS_AUTO_SYNC` | `true` |
| `RESEND_API_KEY` | chiave Resend |
| `SENDER_EMAIL` | `noreply@aia-legnano.it` |
| `NOTIFY_EMAIL` | `legnano@aia-figc.it` |

Aggiorna `frontend/vercel.json` con l’URL `*.onrender.com`, poi ridistribuisci Vercel.

**Dominio custom API (opzionale):** CNAME `api` → host Render (se il piano lo consente) oppure resta sul proxy Vercel `/api`.

---

## Passo 3 — DNS Aruba

Nel pannello DNS del dominio **aia-legnano.it** (senza toccare i record **MX** mail):

| Host | Tipo | Valore | Note |
|------|------|--------|------|
| `www` | CNAME | `cname.vercel-dns.com` | Vercel mostra il valore esatto in Domains |
| `@` | A / ALIAS / redirect | come indicato da Vercel per apex | oppure redirect www via pannello Aruba |
| `api` | CNAME | target Railway | solo quando attivi dominio API su Railway |

**Non modificare** i record MX/SPF esistenti della casella Aruba finché Resend non è configurato per `noreply@aia-legnano.it` (record DKIM/SPF di Resend sul dominio).

---

## Passo 4 — Cutover (ordine consigliato)

1. Verifica backend: `curl https://aia-production-00a9.up.railway.app/api/health`
2. Verifica frontend Vercel con proxy: `curl https://<tuo-progetto>.vercel.app/api/health`
3. Abbassa TTL DNS a 300s (se possibile) 24h prima
4. Aggiorna CNAME `www` → Vercel
5. Attendi propagazione; apri `https://www.aia-legnano.it`
6. Test: home, news, designazioni, form contatti, login admin, area associati
7. (Opzionale) Attiva `api.aia-legnano.it` su Railway + CNAME
8. Aggiorna `PORTAL_FRONTEND_URL` e `PUBLIC_API_URL` su Railway
9. Backup/snapshot sito WordPress Aruba prima di dismetterlo

Script di smoke test locale:

```bash
./scripts/verify_go_live.sh https://www.aia-legnano.it
```

---

## Rollback

- Ripristina CNAME `www` al hosting WordPress Aruba (conserva screenshot/export da `scripts/export_wp_rest.py`)
- Il backend Railway resta attivo; puoi tornare al dominio Vercel temporaneo

---

## Riferimenti

- [`GO_LIVE.md`](GO_LIVE.md) — export contenuti, email, checklist
- [`DEPLOYMENT.md`](DEPLOYMENT.md) — variabili e hosting
- [`BACKUP.md`](BACKUP.md) — dump Mongo e upload
