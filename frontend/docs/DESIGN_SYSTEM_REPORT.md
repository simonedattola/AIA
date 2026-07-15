# Design System — Report implementazione

**Data:** 21 maggio 2026  
**Scope:** solo infrastruttura (Fasi 1–2). Nessuna pagina esistente è stata migrata.

---

## Fase 1 — Token condivisi

### Tipografia

| Token | Dimensione | Utility Tailwind | Classe CSS |
|-------|------------|------------------|------------|
| Page Title | 36px → 40px (sm+) | `text-ds-page sm:text-ds-page-lg` | `.ds-page-title` |
| Section Title | 32px → 36px (sm+) | `text-ds-section sm:text-ds-section-lg` | `.ds-section-title` |
| Subsection Title | 24px | `text-ds-subsection` | `.ds-subsection-title` |
| Card Title | 20px | `text-ds-card` | `.ds-card-title` |
| Body | 16px | `text-ds-body` | `.ds-body` |
| Small | 14px | `text-ds-small` | `.ds-small` |
| Caption | 12px | `text-ds-caption` | `.ds-caption` |
| Eyebrow | 12px uppercase | — | `.ds-eyebrow` |

### Spacing, radius, ombre, bottoni

| Token | Valore | Tailwind |
|-------|--------|----------|
| Section spacing | 48px → 64px (lg) | `py-ds-section-y lg:py-ds-section-y-lg` |
| Card padding | 20px / 24px | `p-ds-card` / `p-ds-card-lg` |
| Grid gap | 24px | `gap-ds-grid` |
| Button default | 44px | `h-ds-btn` |
| Button sm | 36px | `h-ds-btn-sm` |
| Button xs | 32px | `h-ds-btn-xs` |
| Radius sm–xl | 4–12px | `rounded-ds-sm` … `rounded-ds-xl` |
| Shadow sm / md / lift | — | `shadow-ds-sm` … `shadow-ds-lift` |

Variabili CSS in `src/styles/design-tokens.css`. Estensioni Tailwind in `tailwind.config.js`.

---

## Fase 2 — Componenti riutilizzabili

Import unificato:

```jsx
import { PageTitle, SectionTitle, Card, Button } from '@/design-system';
```

| Componente | File | Note |
|------------|------|------|
| `<PageTitle>` | `components/design-system/Typography.jsx` | default `h1` |
| `<SectionTitle>` | idem | default `h2` |
| `<SubsectionTitle>` | idem | default `h3` |
| `<CardTitle>` | idem | default `h4` |
| `<Eyebrow>` | idem | default `span` |
| `<BodyText>` / `<SmallText>` / `<CaptionText>` | idem | helper migrazione |
| `<Card>` | `components/design-system/Card.jsx` | `interactive`, `padding`, `radius`, `shadow` |
| `<CardMedia>` / `<CardBody>` | idem | composizione card |
| `<Button>` | `components/design-system/Button.jsx` | `variant`, `size`, `to`, `href` |
| `<Section>` | `components/design-system/Section.jsx` | padding verticale DS |

Oggetto `typography`, `spacing`, `card`, `button` in `design-system/tokens.js` per migrazione graduale senza sostituire subito ogni JSX.

---

## File creati

| Percorso | Descrizione |
|----------|-------------|
| `src/styles/design-tokens.css` | CSS custom properties (`:root`) |
| `src/styles/design-system-components.css` | Classi utility `.ds-*` in `@layer components` |
| `src/design-system/tokens.js` | Mappe classi Tailwind per migrazione |
| `src/design-system/index.js` | Barrel export pubblico |
| `src/design-system/README.md` | Guida rapida utilizzo |
| `src/components/design-system/Typography.jsx` | Titoli + testo |
| `src/components/design-system/Card.jsx` | Card + sotto-componenti |
| `src/components/design-system/Button.jsx` | Bottone unificato |
| `src/components/design-system/Section.jsx` | Wrapper sezione |
| `src/components/design-system/index.js` | Re-export componenti |
| `docs/DESIGN_SYSTEM_REPORT.md` | Questo report |

---

## File modificati

| Percorso | Modifica |
|----------|----------|
| `tailwind.config.js` | `fontSize`, `spacing`, `borderRadius`, `boxShadow` con prefisso `ds-*` |
| `src/index.css` | Import token + `design-system-components.css` dopo `@tailwind components` |

---

## Fase 3 — Componenti ancora da migrare

Pattern legacy ancora in uso nel codebase (`btn-primary`, `card-lift`, `site-section`, `text-3xl`/`text-4xl` ad hoc).

### Priorità alta — componenti condivisi

Questi file impattano molte pagine; migrarli per primi moltiplica l’effetto:

| File | Pattern da sostituire |
|------|----------------------|
| `components/PageHeader.jsx` | `text-4xl sm:text-5xl`, eyebrow ad hoc |
| `components/admin/admin-ui.jsx` | `AdminPageHeader` (`text-3xl`), `AdminPanel`, `AdminStatCard` (`card-lift`) |
| `components/cms/CmsPageShell.jsx` | `site-section`, titoli inline |
| `blocks/BlockRenderer.jsx` | ~21 `btn-primary` / `card-lift` / titoli misti |
| `blocks/DynamicPageBlocks.jsx` | ~12 pattern card/bottoni/titoli |

### Pagine pubbliche

| File |
|------|
| `pages/AssociatiPage.jsx` |
| `pages/CustomPage.jsx` |
| `pages/NewsDetailPage.jsx` |
| `pages/NewsListPage.jsx` (via `PageHeader`) |
| `pages/ChiSiamoPage.jsx` |
| `pages/ContattiPage.jsx` |
| `pages/DiventaArbitroPage.jsx` |
| `pages/ArbitriPage.jsx` |
| `pages/SystemCmsPage.jsx` (indiretto via shell/blocks) |

### Area associati (portal)

| File |
|------|
| `pages/portal/PortalDashboardPage.jsx` |
| `pages/portal/PortalCalendarioPage.jsx` |
| `pages/portal/PortalComunicazioniPage.jsx` |
| `pages/portal/PortalMediaPage.jsx` |
| `pages/portal/PortalAreaTecnicaPage.jsx` |
| `pages/portal/PortalNewsPage.jsx` |
| `pages/portal/PortalPremiPage.jsx` |
| `pages/portal/PortalProfiloPage.jsx` |
| `pages/portal/PortalStoricoPage.jsx` |
| `pages/portal/PortalLoginPage.jsx` |
| `components/portal/PortalEventCard.jsx` |
| `components/portal/PortalDesignationCard.jsx` |
| `components/portal/AssociatoLayout.jsx` |
| `components/members/MemberProfileContent.jsx` |

### Area admin

| File |
|------|
| `pages/admin/AdminDashboardPage.jsx` |
| `pages/admin/AdminArticlesPage.jsx` |
| `pages/admin/AdminArticleEditPage.jsx` |
| `pages/admin/AdminEventsPage.jsx` |
| `pages/admin/AdminMembersPage.jsx` |
| `pages/admin/AdminGalleryPage.jsx` |
| `pages/admin/AdminDocumentsPage.jsx` |
| `pages/admin/AdminPagesPage.jsx` |
| `pages/admin/AdminPageEditPage.jsx` |
| `pages/admin/AdminComunicazioniPage.jsx` |
| `pages/admin/AdminDesignationsPage.jsx` |
| `pages/admin/AdminTestimonialsPage.jsx` |
| `pages/admin/AdminSettingsPage.jsx` |
| `pages/admin/AdminLeadsPage.jsx` |
| `pages/admin/AdminMessagesPage.jsx` |
| `pages/admin/AdminLoginPage.jsx` |
| `pages/admin/AdminLayout.jsx` |
| `components/admin/GalleryCropModal.jsx` |
| `components/admin/EventPresenzePanel.jsx` |

### Altri componenti UI

| File |
|------|
| `components/GalleryCarousel.jsx` |
| `components/SiteHeader.jsx` |
| `components/SiteFooter.jsx` |
| `components/documents/DocumentsDownloadLayout.jsx` |
| `components/events/EventDetailModal.jsx` |
| `blocks/PageBuilder.jsx` |
| `blocks/BlockEditors.jsx` |

### CSS legacy da deprecare (dopo migrazione)

In `src/index.css`:

- `.btn-primary`, `.btn-secondary`, `.btn-outline`
- `.card-lift`
- `.site-section`

Coesistono con il DS fino al completamento della migrazione.

---

## Ordine di migrazione consigliato

1. `admin-ui.jsx` → `AdminPageHeader` usa `<PageTitle>`, `AdminPanel` usa `<Card>`
2. `PageHeader.jsx` → hero pubblico (variante speciale di `<PageTitle>` su sfondo navy)
3. `BlockRenderer.jsx` + `DynamicPageBlocks.jsx`
4. Pagine admin una per una
5. Portal e pagine pubbliche
6. Rimozione classi legacy da `index.css`

---

## Verifica

```bash
cd frontend && npm run build
```

Nessun import del DS nelle pagine esistenti: zero regressioni attese finché non si avvia la migrazione.
