# Area Riservata Associati — AIA Legnano

Applicazione web per associati arbitrali: dashboard, calendario, presenze, area tecnica, storico gare, notifiche, premi, news, media e messaggistica interna.

## Stack

- **Next.js 14** (App Router) + TypeScript + Tailwind CSS
- **Prisma** + SQLite (demo) o PostgreSQL (produzione)
- **NextAuth.js** — login email/password, sessione JWT
- react-hook-form, zod, date-fns, react-big-calendar, react-hot-toast, bcrypt, nodemailer, recharts

## Avvio rapido

```bash
cd area-riservata
npm install
cp .env.example .env
npx prisma migrate dev --name init
npm run seed
npm run dev
```

Apri [http://localhost:3000](http://localhost:3000).

## Accesso associati

- **Username:** codice meccanografico AIA (impostato in Admin → Associati)
- **Password iniziale:** `nome.cognome` in minuscolo (es. Simone Dattola → `simone.dattola`)
- L’associato può cambiare la password da **Profilo** nel portale

| Esempio | Codice | Password iniziale |
|---------|--------|-------------------|
| Simone Dattola | `86178903` | `simone.dattola` |
| Admin portale | `00000001` | `admin.demo` |

Salvando un associato in admin con codice meccanografico, il backend sincronizza l’account sul portale (`PORTAL_URL` + `PORTAL_SYNC_SECRET`).

## PostgreSQL

In `.env`:

```
DATABASE_URL="postgresql://user:password@localhost:5432/area_riservata?schema=public"
```

In `prisma/schema.prisma` cambia `provider` da `sqlite` a `postgresql`, poi:

```bash
npx prisma migrate dev
npm run seed
```

## Funzionalità

| Percorso | Descrizione |
|----------|-------------|
| `/dashboard` | Widget designazioni, eventi, news, comunicazioni, notifiche |
| `/profilo` | Foto, biografia, contatti, visibilità, cambio password |
| `/calendario` | Vista mese/settimana, presenze, calendario personale, reminder |
| `/area-tecnica` | Documenti RTO, quiz, preferiti |
| `/storico` | Gare arbitrate, statistiche, grafico Recharts |
| `/news` | Feed personalizzato (citazioni, categoria, successi) |
| `/premi` | Traguardi e riconoscimenti |
| `/media` | Galleria foto, download, preferiti |
| `/messaggi` | Chat con consiglio/osservatori (polling 30s) |
| `/admin/eventi` | Lista eventi (ADMIN/OSSERVATORE) |
| `/admin/presenze/[id]` | Gestione presenze partecipanti |

## Email reminder

Configura SMTP in `.env` (`SMTP_HOST`, `SMTP_USER`, …). Senza SMTP i reminder vengono registrati nel DB e loggati in console.

## Script

- `npm run dev` — sviluppo
- `npm run build` — build produzione
- `npm run seed` — dati demo
- `npm run db:migrate` — migrazioni Prisma

## Integrazione sito pubblico

- Nel menu del sito React compare **Area riservata** (`/area/riservata` → redirect a questo portale, default `http://localhost:3001`)
- Variabile frontend: `REACT_APP_AREA_RISERVATA_URL`

## Note autenticazione

Solo **codice meccanografico + password** (nessun provider social). La registrazione pubblica è disabilitata.
