# Design System — Report migrazione Fase 2

**Data:** 21 maggio 2026  
**Scope:** estensione DS (`HeroTitle`, `CtaTitle`) + `BlockRenderer.jsx`, `DynamicPageBlocks.jsx`, aggiornamento `PageHeader.jsx`

---

## Estensioni Design System

| Aggiunta | Descrizione |
|----------|-------------|
| `HeroTitle` | Token `text-ds-hero` → `sm:ds-hero-sm` → `lg:ds-hero-lg` (36→48→60px) |
| `CtaTitle` | Token `text-ds-cta` → `sm:ds-cta-md` → `lg:ds-cta-lg` (30→36→48px) |
| Token `--ds-text-section` | Allineato a 30px/36px (pattern CMS `text-3xl`/`text-4xl`) |

File toccati: `design-tokens.css`, `tailwind.config.js`, `Typography.jsx`, `tokens.js`, export barrel.

---

## File modificati

| File | Tipo |
|------|------|
| `src/styles/design-tokens.css` | Token hero + CTA + section CMS |
| `tailwind.config.js` | `fontSize` ds-hero*, ds-cta* |
| `src/components/design-system/Typography.jsx` | `HeroTitle`, `CtaTitle` |
| `src/design-system/tokens.js` | Mappe typography |
| `src/components/design-system/index.js` | Export |
| `src/design-system/index.js` | Export |
| `src/components/PageHeader.jsx` | `HeroTitle` al posto di `PageTitle` + override |
| `src/blocks/BlockRenderer.jsx` | Migrazione completa blocchi statici |
| `src/blocks/DynamicPageBlocks.jsx` | Migrazione blocchi dinamici |

---

## Titoli migrati

| Componente DS | BlockRenderer | DynamicPageBlocks | Totale |
|---------------|---------------|-------------------|--------|
| `HeroTitle` | 3 | 0 | **3** |
| `CtaTitle` | 1 | 1 | **2** |
| `SectionTitle` | 11 | 1 (SectionIntro) | **12** |
| `SubsectionTitle` | 3 | 4 | **7** |
| `CardTitle` | 6 | 6 | **12** |
| `Eyebrow` | 18 | 8 | **26** |
| **Totale elementi tipografici DS** | **42** | **20** | **62** |

*(SectionIntro in DynamicPageBlocks alimenta 6 blocchi: designations, members, news, events, contact, organigramma.)*

---

## Card migrate

| File | Card `<Card>` | Note |
|------|---------------|------|
| BlockRenderer | 10 | FAQ, stats (light), gallery thumb, news slider, event card, testimonials |
| DynamicPageBlocks | 7 | members grid, news grid, events calendar item, contact form, person card, president card |
| **Totale** | **17** | Escluse card navy/gradient (stats su sfondo navy, Instagram widget) |

---

## Bottoni migrati

| Pattern eliminato | Sostituzione | Occorrenze |
|-------------------|--------------|------------|
| `btn-primary` | `<Button variant="primary">` | 4 |
| `btn-secondary` | `<Button variant="secondary">` via `CtaLink` | 2 |
| `btn-outline` | `<Button variant="outline">` | 3 |
| `CtaLink` + classi legacy | `CtaLink` + `variant` prop → `<Button>` | 6 |

---

## Classi Tailwind eliminate (principali)

| Classe / pattern | Occorrenze rimosse (stima) |
|------------------|----------------------------|
| `.eyebrow` | ~20 |
| `font-display text-3xl sm:text-4xl font-bold` | ~15 |
| `font-display text-3xl sm:text-4xl lg:text-5xl` | 2 |
| `font-display text-4xl sm:text-5xl lg:text-6xl` | 2 |
| `font-display text-2xl font-bold` | ~8 |
| `font-display text-xl font-semibold` | ~6 |
| `.card-lift` | 10 |
| `.btn-primary` / `.btn-outline` / `.btn-secondary` | 9 |
| `bg-white rounded-lg border border-slate-200` (wrapper card) | ~12 |
| `gap-6` → `gap-ds-grid` | 6 |
| `p-5` / `p-6` → `p-ds-card` / `p-ds-card-lg` | 8 |

**Rimanenti intenzionali** (non titoli di sezione): iniziali avatar (`font-display text-2xl`), step timeline (`text-xl`), date evento (`text-2xl`), placeholder foto.

---

## Copertura DS stimata

| Ambito | Prima (Fase 1) | Dopo (Fase 2) |
|--------|----------------|---------------|
| Infrastruttura token + componenti | 100% | 100% |
| Componenti condivisi priorità alta (5) | 40% | **100%** |
| Blocchi CMS (`BlockRenderer` + `DynamicPageBlocks`) | 0% | **~95%** |
| File con pattern legacy residui | ~43 | **~28** |
| **Copertura globale progetto** | ~12% | **~35%** |

Tutte le pagine pubbliche basate su CMS ereditano il DS tramite i blocchi migrati.

---

## Regressioni visive possibili

1. **SectionTitle** — token section ora 30px/36px (allineato al CMS); coerente con il precedente.
2. **Card interactive** — hover border default `navy-600`; dove serviva `navy-300` è esplicitato in `className` (eventi calendario).
3. **Card padding** — `p-ds-card` (20px) sostituisce `p-5`; `p-ds-card-lg` (24px) sostituisce `p-6`: equivalenti.
4. **Button CTA** — altezza token `h-ds-btn-sm` vs legacy `.btn-outline.text-sm`: differenza ≤2px.
5. **President card** — `CtaTitle` con `text-4xl lg:text-5xl` sovrascrive il token CTA base (30px) per preservare il layout hero presidente.
6. **Stat label con Eyebrow + normal-case** — mantiene caption 12px; uppercase rimosso via `normal-case` dove il label non è eyebrow semantico.
7. **Gallery button-card** — `Card as="button"` aggiunge bordo bianco; hover lift DS vs `.card-lift` (stesso translate -4px).

---

## Verifica

```bash
cd frontend && npm run build
```

Build completata con successo.
