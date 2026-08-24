# Go-live: da localhost a produzione

Come portare online i contenuti che vedi in locale e collegare il dominio Aruba.

## Perché il link temporaneo “non ha i contenuti”

- Su `localhost` i dati sono in **Mongo locale** + file in `backend/uploads`.
- Le immagini erano esposte come `http://localhost:8000/api/uploads/...`: dal telefono quel host non esiste.
- Fix applicata: con `PUBLIC_API_URL` vuoto/localhost le API restituiscono path **relativi** `/api/uploads/...` (ok con proxy/tunnel).

## Cosa fare adesso (ordine)

### 1) Anteprima tunnel (stesso PC)

1. Backend + frontend locali avviati.
2. `PUBLIC_API_URL=` (vuoto) in `backend/.env`.
3. Tunnel sul frontend `:3000` (proxy `/api` → `:8000`).
4. Hard refresh sul telefono.

### 2) Pacchetto contenuti locali

```bash
chmod +x scripts/export_local_content.sh
./scripts/export_local_content.sh
```

Produce `backups/local-export-…/` con dump Mongo + `uploads/`.

### 3) Export sito WordPress vecchio (pubblico)

```bash
python3 scripts/export_wp_rest.py --out backups/wp-export
```

Scarica posts/pages/media/categories via WP REST (77+ articoli su aia-legnano.it).

### 4) Hosting consigliato (non tutto su Aruba shared)

| Pezzo | Dove |
|-------|------|
| Dominio + DNS + **casella mail** | **Aruba** (già pagato) |
| Frontend | **Vercel** |
| Backend FastAPI | Railway / Render / Fly / VPS |
| Database | **MongoDB Atlas** (free tier) |
| Upload | disco del backend o S3 |

L’hosting Aruba ~65€/anno è tipicamente PHP/MySQL: **non** adatto a FastAPI+Mongo.

### 5) Email (Resend + casella sezione)

Il backend invia con **Resend** (non SMTP Aruba). Destinatario sezione di default: `legnano@aia-figc.it`.

Variabili su Railway (backend):

| Variabile | Valore tipico |
|-----------|----------------|
| `RESEND_API_KEY` | chiave `re_…` da resend.com (obbligatoria per inviare) |
| `SENDER_EMAIL` | `noreply@aia-legnano.it` (dominio verificato in Resend) |
| `NOTIFY_EMAIL` | `legnano@aia-figc.it` |
| `PORTAL_FRONTEND_URL` | `https://aia-virid.vercel.app` (link nelle mail agli associati) |

Flussi:

- **Alla sezione** (`NOTIFY_EMAIL`): contatti sito, candidature corso, testimonianze e foto da approvare, commenti su comunicazioni.
- **Agli associati** (opt-in in Area associati → Profilo): comunicazioni interne, messaggi, invito/promemoria eventi.

Senza `RESEND_API_KEY` i form salvano comunque i dati; le email vengono saltate (log `[mailer] Skipped`).

Nel pannello Aruba mantieni MX e la casella `legnano@aia-figc.it` (o alias) per ricevere. Per DKIM/SPF del mittente `noreply@aia-legnano.it` configura i record DNS indicati da Resend.

### 6) DNS cutover (quando API+frontend sono online)

- `www` / `@` → Vercel
- `api` (opzionale) → backend
- Mantieni mail MX Aruba invariati

### 7) FTP Aruba da questo ambiente cloud

FTP/SFTP verso `62.149.141.10` risulta **bloccato/resettato** dalla rete agent.  
Esegui il backup WP dal tuo PC con FileZilla:

- Host: quello Aruba del pannello  
- User/password hosting  
- Scarica `www` / `public_html` + DB da phpMyAdmin

**Non** mettere password Aruba nel repo Git.

## Credenziali

- Password già incollate in chat: **ruotale** (Aruba + WP + admin nuovo).
- Admin del sito nuovo = `ADMIN_EMAIL` / `ADMIN_PASSWORD` in env di produzione (non le password WP).

## Checklist rapida

- [ ] Export locale (`scripts/export_local_content.sh`)
- [ ] Export WP REST
- [ ] Atlas cluster + restore/import
- [ ] Deploy backend + `PUBLIC_API_URL=https://api…`
- [ ] Deploy frontend Vercel + `REACT_APP_BACKEND_URL`
- [ ] Casella mail Aruba + form
- [ ] DNS
- [ ] Rotazione password
