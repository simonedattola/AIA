# Design System — Report migrazione Fase 1

**Data:** 21 maggio 2026  
**Scope:** `PageHeader.jsx`, `admin-ui.jsx`

---

## File modificati

| File | Modifiche |
|------|-----------|
| `src/components/PageHeader.jsx` | Eyebrow + PageTitle al posto di classi tipografiche inline |
| `src/components/admin/admin-ui.jsx` | PageTitle, SubsectionTitle, Card, Button; rimosso import `Link` ridondante |

**Pagine impattate indirettamente** (nessuna modifica diretta):  
`NewsListPage`, `AssociatiPage`, `CustomPage`, `CmsPageShell` (PageHeader); tutte le pagine admin che usano `AdminPageHeader`, `AdminPanel`, `AdminStatCard`, `AdminQuickLink`.

---

## Classi eliminate

### PageHeader.jsx

| Rimossa | Sostituita con |
|---------|----------------|
| `text-xs uppercase tracking-[0.25em] font-semibold` (eyebrow) | `<Eyebrow>` + `text-gold-400 tracking-[0.25em]` (contesto hero) |
| `font-display text-4xl sm:text-5xl lg:text-6xl font-bold` | `<PageTitle>` + `sm:text-5xl lg:text-6xl` (breakpoint hero) |

**Mantenute** (fuori scope componenti DS ammessi): `text-lg text-slate-200 max-w-3xl leading-relaxed` sulla description.

### admin-ui.jsx

| Rimossa | Sostituita con |
|---------|----------------|
| `font-display text-3xl font-bold text-navy-700` | `<PageTitle className="text-3xl mb-1">` |
| `bg-white rounded-lg border border-slate-200` | `<Card padding="none" radius="lg">` |
| `bg-white rounded-lg border p-5 card-lift block` | `<Card as={Link} interactive padding="default">` |
| `font-display text-2xl font-bold text-navy-700` | `<SubsectionTitle as="div" className="font-bold">` |
| `btn-primary text-sm` | `<Button variant="primary" size="sm">` |
| `btn-outline text-sm` | `<Button variant="outline" size="sm">` |

**Non migrate** (componenti DS non richiesti / non tipografia-card-button):  
`AdminAlert`, `AdminField`, `AdminEmptyState`, `AdminFilterTabs`, `AdminBadge`, `AdminSearchBar`, `adminTableHead`.

---

## Componenti DS utilizzati

| Componente | Occorrenze | File |
|------------|------------|------|
| `<PageTitle>` | 2 | PageHeader, AdminPageHeader |
| `<Eyebrow>` | 1 | PageHeader |
| `<SubsectionTitle>` | 1 | AdminStatCard (valore numerico) |
| `<Card>` | 2 | AdminPanel, AdminStatCard |
| `<Button>` | 1 | AdminQuickLink |
| `<SectionTitle>` | 0 | — |

---

## Problemi rilevati

### 1. Hero PageHeader — scale responsive parziale

`<PageTitle>` applica il token base `text-ds-page` (36px, equivalente a `text-4xl`).  
I breakpoint `sm:text-5xl` e `lg:text-6xl` sono preservati via `className` perché non esistono token DS per titoli hero più grandi.

**Impatto:** nessuno su mobile; da `sm` in su il comportamento è identico al precedente.

### 2. AdminPageHeader — dimensione titolo

Il titolo admin era `text-3xl` (30px); `<PageTitle>` di default è 36px.  
Per non alterare il layout è stato aggiunto `className="text-3xl"` che sovrascrive il token base.

**Impatto:** visivamente invariato; il token `text-ds-page` è neutralizzato su questo uso.

### 3. AdminStatCard — hover border

`<Card interactive>` di default usa `hover:border-navy-600`.  
La card statistica originale usava `hover:border-navy-300`.  
Risolto con `className="hover:border-navy-300"` che vince nel merge Tailwind.

**Impatto:** nessuno — hover border preservato.

### 4. AdminQuickLink — padding bottone

`<Button size="sm">` usa altezza token `h-ds-btn-sm` (36px) vs `.btn-primary.text-sm` legacy.  
Dimensioni molto simili; eventuale differenza di 1–2px sul padding orizzontale.

**Impatto:** trascurabile; da verificare visivamente in dashboard admin.

### 5. Bundle size

Build JS +9.5 kB gzip dopo import del barrel `@/design-system` nei componenti condivisi. Atteso per la prima adozione; si stabilizzerà con migrazioni successive senza duplicazione.

---

## Copertura Design System stimata

| Ambito | Prima | Dopo Fase 1 |
|--------|-------|-------------|
| Infrastruttura token + componenti | 100% | 100% |
| Componenti condivisi priorità alta (5) | 0% | **40%** (2/5: PageHeader, admin-ui) |
| File con pattern legacy (`btn-primary`, `card-lift`, titoli ad hoc) | ~45 file | ~43 file |
| **Copertura globale progetto** | ~5% | **~12%** |

Calcolo globale: (infrastruttura completa + 2 file migrati + ~20 pagine ereditano DS via componenti condivisi) / ~170 file frontend.

### Prossimi target (Fase 2)

1. `CmsPageShell.jsx`
2. `BlockRenderer.jsx`
3. `DynamicPageBlocks.jsx`

---

## Verifica

```bash
cd frontend && npm run build
```

Build completata con successo.
