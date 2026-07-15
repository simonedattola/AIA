# Design System AIA Legnano

Infrastruttura centralizzata per tipografia, spacing, card e bottoni.  
I componenti DS convivono con utility legacy residue (es. `.site-section`) dove la migrazione layout non è ancora completa. Bottoni e card hover usano `@/design-system`.

## Utilizzo

```jsx
import { PageTitle, SectionTitle, Card, Button, FilterPill } from '@/design-system';

<PageTitle variant="compact">Titolo pagina</PageTitle>
<SectionTitle>Titolo sezione</SectionTitle>
<Card as={Link} to="/path" interactive padding="default">…</Card>
<Card variant="accent" padding="default">Form lead / testimonianze</Card>
<Button variant="primary" size="default">Salva</Button>
<FilterPill active={isActive} onClick={toggle}>Filtro</FilterPill>
```

Classi token per migrazione graduale:

```jsx
import { typography, spacing } from '@/design-system';

<h2 className={typography.sectionTitle}>…</h2>
<section className={spacing.section}>…</section>
```

## Token

| Token | Valore | Classe utility |
|-------|--------|----------------|
| Page title | 36px → 40px | `text-ds-page sm:text-ds-page-lg` |
| Section title | 32px → 36px | `text-ds-section sm:text-ds-section-lg` |
| Subsection title | 24px | `text-ds-subsection` |
| Card title | 20px | `text-ds-card` |
| Body | 16px | `text-ds-body` |
| Small | 14px | `text-ds-small` |
| Caption | 12px | `text-ds-caption` |
| Section spacing | 48px → 64px | `py-ds-section-y lg:py-ds-section-y-lg` |
| Card padding | 20px / 24px | `p-ds-card` / `p-ds-card-lg` |
| Grid gap | 24px | `gap-ds-grid` |
| Button heights | 44 / 36 / 32px | `h-ds-btn` / `h-ds-btn-sm` / `h-ds-btn-xs` |
| Radius | 4–12px | `rounded-ds-sm` … `rounded-ds-xl` |
| Shadows | sm / md / lift | `shadow-ds-sm` … |

Variabili CSS: `src/styles/design-tokens.css`

## Accessibilità

### Gerarchia heading e prop `as`

Usare **un solo `h1` per pagina**. Default dei componenti tipografici:

| Componente | Default `as` | Uso tipico |
|------------|--------------|------------|
| `PageTitle` | `h1` | Titolo principale pagina |
| `HeroTitle` | `h1` | Hero full-bleed (non combinare con `PageTitle` sulla stessa pagina senza cambiare `as`) |
| `SectionTitle` | `h2` | Sezione principale |
| `CtaTitle` | `h2` | Banner CTA |
| `SubsectionTitle` | `h3` | Sotto-sezione |
| `CardTitle` | `h4` | Titolo dentro card (usare `as="h2"` o `as="h3"` se il contesto lo richiede) |
| `Eyebrow` | `span` | Etichetta sopra un titolo |

Regolare `as` quando la gerarchia del documento richiede un livello diverso dal default.

### `Card interactive`

Preferire sempre elementi semantici focusabili:

```jsx
<Card as={Link} to="/associati" interactive>…</Card>
<Card as="button" type="button" onClick={…} interactive>…</Card>
```

Evitare `<Card interactive>` su un `div` senza `role`/`tabIndex`: in sviluppo viene emesso un warning e applicato un fallback (`role="button"`, `tabIndex={0}`). Il fallback non sostituisce un link o un bottone vero.

### Filtri (`FilterPill`)

`FilterPill` espone `aria-pressed={active}` per comunicare lo stato selezionato agli screen reader.

### Focus visibile e contrasto

`Button`, `Card` (interactive) e `FilterPill` usano `focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2`.  
I colori principali (`text-navy-700`, `text-white` su `bg-navy-600`) rispettano WCAG AA. `CaptionText` usa `text-slate-600` per margine di contrasto su testo piccolo.

### `Button` disabilitato come link

Con `to` o `href` e `disabled={true}`, il componente renderizza un `<span aria-disabled="true">` non navigabile al posto del link.

## Responsive (mobile-first)

- Pulsanti DS: `min-h-[44px]` su tutte le taglie.
- Griglie: `grid-cols-1` di default, breakpoint `sm:` / `md:` / `lg:`.
- Tabelle admin: wrapper `overflow-x-auto`.
- Card: padding `p-4 sm:p-5` su mobile dove serve stack verticale.

## Testing

I componenti accettano `data-testid` e altre props tramite spread (`...props`). Convenzione suggerita:

```jsx
<Button data-testid="save-profile" variant="primary">Salva</Button>
<Card data-testid="member-card-john-doe" interactive as={Link} to="…">…</Card>
<FilterPill data-testid="filter-arbitri" active={…}>Arbitri</FilterPill>
```

Usare prefissi descrittivi legati alla pagina o al flusso sotto test.
