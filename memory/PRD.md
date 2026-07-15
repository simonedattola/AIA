# AIA Legnano – Product Requirements Document

## Original problem statement
Trasformare il sito demo della Sezione AIA Legnano (Associazione Italiana Arbitri – FIGC) in una piattaforma web di produzione: istituzionale, premium, gestibile interamente da pannello admin via browser, con identità visiva ufficiale AIA, CMS articoli, organigramma, designazioni, associati, eventi, corso arbitri con form lead, contatti.

## Stack scelto (su richiesta utente)
- **Frontend**: React 19 (CRA) + Tailwind CSS + Outfit/IBM Plex Sans + TipTap editor
- **Backend**: FastAPI + Motor (MongoDB async) + bcrypt + JWT (python-jose) + bleach (sanitize HTML) + Resend (email, opzionale)
- **Database**: MongoDB (collections: `site_settings`, `nav_items`, `pages`, `articles`, `events`, `officials`, `members`, `designations`, `leads`, `contact_messages`, `admin_users`, `media`)

## Brand identity
- Loghi ufficiali AIA Legnano + AIA FIGC nazionale in `/app/frontend/public/brand/`
- Palette: blu `#004587` + blu secondario `#003366` + gold `#D4AF37`
- Typography: Outfit (display) + IBM Plex Sans (body)

## Architecture / Auth
- Admin singolo seedato da `.env` (`ADMIN_EMAIL`, `ADMIN_PASSWORD`)
- JWT 24h, bearer header
- HTML sanitizzato lato server (whitelist tag sicuri) prima del salvataggio

## ✅ Implementato (14/05/2026)

### Pubblico
- Homepage istituzionale (hero stadio, statistiche, ultime news, prossimi eventi, presidente, CTA Corso Arbitri)
- News listing con filtri categoria
- News detail con prose-aia (paragrafi distanziati, h2/h3 stilizzati, blockquote, immagini inline) — bug "paragrafi attaccati" risolto
- Diventa Arbitro: storytelling, 6 benefici, timeline 5 step, form lead, FAQ accordion
- Chi Siamo: storia, presidente full-width, griglia consiglio direttivo, numeri sezione
- Designazioni: tabella filtrabile + ricerca + responsive cards mobile
- Associati: ricerca live, filtri (arbitri/osservatori), profili individuali con storico designazioni
- Eventi: cards con date badge, separazione upcoming/passati
- Contatti: form + info istituzionali + social
- Header sticky con logo + CTA "Diventa Arbitro" in evidenza
- Footer istituzionale con loghi, social, contatti, link rapidi

### Admin panel completo
- Login JWT con credenziali stampate solo nel `.env` (nessuna password in vista)
- Dashboard con stats e azioni rapide
- CRUD Articoli con editor TipTap (h2/h3/h4, bold, italic, ul/ol, blockquote, link, immagini, hr, undo/redo)
- Anteprima live articoli
- Upload media (immagini → `/api/uploads/`)
- CRUD Eventi, Organigramma, Associati, Designazioni
- Gestione Lead corso arbitri (status: nuova/contattata/archiviata)
- Gestione Messaggi contatti
- Impostazioni sito (contatti, social, fondazione, mappa, portale formazione)

### Backend API
- Public: `/api/public/{settings, nav, pages/:slug, articles, articles/:slug, categories, events, officials, members, members/:slug, designations, stats}`
- Forms: `/api/public/forms/{corso-arbitri, contatti}`
- Admin: full CRUD su tutte le entità + `/api/admin/{login, me, dashboard, upload, media}`
- Sanitize HTML su salvataggio (TipTap output)
- Seed idempotente: 10 associati, 8 organi tecnici, 9 articoli reali, 10 eventi, 10 designazioni
- Resend email integration (opzionale: senza key, form salvano comunque su DB)

## Backlog / Next
### P0 (post-MVP)
- Pagina /risorse (taccuino, calcolatore rimborsi, regolamento)
- Pagina /galleria con album
- Scraper designazioni con adapter pattern (CRA Lombardia, AIA nazionale) + cron
- Importer news da aia-legnano.it (WP REST scrape)

### P1
- Area riservata associati (login per accesso a designazioni personali + comunicazioni)
- SEO sitemap.xml + robots.txt dinamici
- OpenGraph per articoli (image dinamica per condivisione social)
- Calendar `.ics` per eventi
- Feed Instagram via Meta Graph API + cache

### P2
- 2FA admin (TOTP)
- Audit log admin operazioni
- Multilingua (en oltre a it)
- Statistiche per associato (grafico designazioni/categoria)

## File structure key
```
/app/backend/
  server.py             # FastAPI entry, startup seed
  app/
    db.py               # Motor client singleton
    models.py           # Pydantic models
    security.py         # JWT + bcrypt
    sanitize.py         # HTML whitelist
    mailer.py           # Resend wrapper (no-op senza key)
    seed.py             # Idempotent seed
    routes/
      public.py         # API pubbliche
      admin.py          # API admin (JWT-guarded)
  seed_data/*.json      # Dati iniziali da codebase precedente

/app/frontend/src/
  App.js                # Routing
  lib/
    api.js              # Axios client + interceptor token
    format.js           # Date formatters IT
    site-context.js     # Settings + nav globali
  components/
    SiteHeader.jsx / SiteFooter.jsx / SiteLayout.jsx
  pages/
    HomePage / NewsListPage / NewsDetailPage / DiventaArbitroPage
    ChiSiamoPage / DesignazioniPage / AssociatiPage / AssociatoProfilePage
    EventiPage / ContattiPage
    admin/
      AdminLoginPage / AdminLayout / AdminDashboardPage
      AdminArticlesPage / AdminArticleEditPage / RichTextEditor
      AdminEventsPage / AdminOfficialsPage / AdminMembersPage
      AdminDesignationsPage / AdminLeadsPage / AdminMessagesPage
      AdminSettingsPage
/app/frontend/public/brand/
  logo-aia-legnano.png  # logo sezionale ufficiale
  logo-aia-figc.png     # logo AIA FIGC nazionale
```

## Test Status (14/05/2026)
- **Backend**: 29/29 pytest passed (100%)
- **Frontend**: 16/16 public scenarios + 9/9 admin flows passed
- **Bug fixato**: routing `/admin/articles/new` ora funziona correttamente (era id=undefined, ora la route `/articles/:id` matcha `new` come slug)
- **Sanitizzazione XSS**: confermata (script tag stripped via bleach)

---

## CMS Componibile (Iteration 2 — 14/05/2026)

### Filosofia
Trasformazione del sito in **piattaforma editoriale composable**: ogni modifica futura deve essere possibile dall'admin senza toccare codice. Approccio incrementale "smart".

### Architettura blocks
- **Page.blocks**: List[Block]; Block = `{id, type, enabled, config}`
- 14 tipi di blocchi schema-driven: Hero, RichText, TextImage, CTA, FAQ, Timeline, Stats, Gallery, NewsSlider, EventsList, Testimonials, Downloads, Embed, Spacer
- Sanitizzazione HTML server-side per rich_text + faq + embed (whitelist iframe per YouTube/maps)
- Registry centralizzato `/blocks/registry.js` + renderers `/blocks/BlockRenderer.jsx` + editors `/blocks/BlockEditors.jsx`

### Page Builder admin (`/admin/pages/:id`)
- **Drag & drop** riordino blocchi via `@dnd-kit/sortable`
- Add/Remove/Duplicate/Toggle visibility per ogni blocco
- Editor specifico per ogni tipo (form schema-driven)
- 3 tab: **Blocchi** (builder) · **Anteprima** (live render) · **Impostazioni pagina** (SEO, slug, menu)
- Pagine di sistema (home, diventa-arbitro, chi-siamo, contatti) protette da delete
- Pagine custom illimitate con slug `/p/:slug`
- Auto-inclusion nel menu principale via flag `showInMenu`

### Pagine migrate a blocks
- **Home**: hero (con stats card) → news_slider → events_list (con presidente) → cta corso arbitri
- **Diventa Arbitro**: hero → text_image → stats (6 benefici) → timeline (5 step) → cta+form lead → faq accordion

### Nuove entità CMS
- **Documents** (downloads): titolo, URL, dimensione, categoria
- **Testimonials**: nome, ruolo, citazione, foto (3 testimonianze seedate)
- **Albums** (galleria foto): model pronto, UI lato pubblico via blocco Gallery

### Nuove API
- `GET /api/public/testimonials`, `/documents`, `/albums`
- `GET/POST/PUT/DELETE /api/admin/{pages,documents,testimonials,albums}`
- `GET /api/public/nav` ora include pagine custom con `showInMenu=true`

### Files key (Iteration 2)
```
/app/backend/app/
  blocks_sanitize.py        # sanitization blocks rich_text/embed
  seed.py                   # +seed_testimonials, +seed_documents, build_system_pages()
/app/frontend/src/blocks/
  registry.js               # 14 block types + defaults
  BlockRenderer.jsx         # 14 public renderers + dispatcher
  BlockEditors.jsx          # 14 admin editors
  PageBuilder.jsx           # @dnd-kit drag-drop UI
/app/frontend/src/pages/
  HomePage.jsx              # ora carica /api/public/pages/home e renderizza blocks
  DiventaArbitroPage.jsx    # idem con /pages/diventa-arbitro
  CustomPage.jsx            # /p/:slug renderer dinamico
  admin/AdminPagesPage.jsx  # lista pagine
  admin/AdminPageEditPage.jsx # page builder + settings + preview
  admin/AdminDocumentsPage.jsx
  admin/AdminTestimonialsPage.jsx
```

### Cosa l'admin può fare ORA senza codice
- Riordinare/abilitare/duplicare/eliminare i 4 blocchi della Homepage
- Modificare titolo Hero, sfondo, CTA, badge
- Cambiare quante news mostrare in homepage, da quale categoria
- Modificare la CTA "Diventa Arbitro" globalmente
- Editare le 5 FAQ del corso arbitri, aggiungere/rimuovere FAQ
- Editare i 5 step della timeline percorso arbitro
- Editare i 6 benefici del corso (stats block)
- Sostituire/aggiungere il form lead nella pagina corso (block CTA con formType=corso-arbitri)
- Creare pagine custom illimitate accessibili a `/p/<slug>` con qualsiasi combinazione dei 14 blocchi
- Far apparire le pagine custom nel menu principale (flag + label + ordine)
- Gestire centralmente testimonianze e documenti download
