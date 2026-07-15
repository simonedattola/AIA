# UI Components (shadcn/ui) — AIA Legnano

Componenti Radix + Tailwind in stile [shadcn/ui](https://ui.shadcn.com/), tematizzati **navy + gold** per coerenza con il brand.

> **Nota:** le pagine pubbliche e l’admin usano principalmente `@/design-system` (`Button`, `Card`, tipografia). Usa questa cartella per dialog, form complessi, tabelle Radix e nuove feature admin che richiedono primitivi shadcn.

## Import

```jsx
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
```

## Button — varianti

| Variant | Uso |
|---------|-----|
| `default` | Azione primaria navy |
| `outline` | Secondaria con bordo navy |
| `secondary` / `accent` | Gold CTA |
| `ghost` | Azioni leggere |
| `link` | Stile link testuale |
| `destructive` | Elimina / pericolo |

```jsx
<Button variant="default" size="default">Salva</Button>
<Button variant="outline" size="sm">Annulla</Button>
<Button variant="accent">Diventa arbitro</Button>
```

Tutte le dimensioni (tranne `link`) rispettano **min-h-[44px]** per touch target WCAG su mobile.

## Card — varianti

```jsx
<Card>
  <CardHeader>
    <CardTitle>Titolo</CardTitle>
  </CardHeader>
  <CardContent>…</CardContent>
</Card>

{/* Form lead, testimonianze, CTA premium */}
<Card variant="accent" className="p-4 sm:p-6">…</Card>
```

`variant="accent"` aggiunge `border-t-4 border-gold-400`.

## Responsive Guidelines (mobile-first)

1. **Griglie:** sempre `grid-cols-1` di default, poi `sm:` / `md:` / `lg:`.
2. **Padding card:** `p-4 sm:p-6` — `CardHeader` / `CardContent` già responsive.
3. **Tabelle:** wrappare con `overflow-x-auto`; tabella interna `min-w-[…]` se necessario.
4. **Touch target:** minimo 44×44px su pulsanti e controlli tap (Button UI e `@/design-system`).
5. **Test viewport:** 375px (iPhone SE), 768px (tablet), 1024px+ (desktop).
6. **Nessuna overflow orizzontale:** evitare `w-[fixed]` senza `max-w-full` su mobile.

## Accessibilità

- Focus: `focus-visible:ring-2 ring-gold-400 ring-offset-2` su Button.
- Icone decorative: `aria-hidden="true"`.
- Pulsanti icona: `aria-label` obbligatorio.
- Per heading e gerarchia documento preferire `@/design-system` (`PageTitle`, `SectionTitle`, prop `as`).

## Testing

Passare `data-testid` come prop nativa:

```jsx
<Button data-testid="dialog-confirm">Conferma</Button>
```

## Come estendere il DS

1. **Nuova variante Button:** aggiungi in `buttonVariants` in `button.jsx` (cva), mantieni `min-h-[44px]`.
2. **Nuova variante Card:** estendi `cardVariants` in `card.jsx`.
3. **Componenti sito pubblico:** preferisci `@/design-system` per tipografia e card interattive (`interactive`, `as={Link}`).
4. **Token condivisi:** colori navy/gold in `tailwind.config.js`; spacing DS in `src/styles/design-tokens.css`.
5. **Non duplicare:** se un pattern esiste in `@/design-system`, riusalo invece di creare classi raw `bg-navy-600`.

Documentazione DS principale: `src/design-system/README.md`.

## Card memoizzate (liste CMS)

Componenti riusabili in `src/components/cards/` (con `React.memo`):

- `MemberGridCard` — griglia associati
- `NewsArticleCard` — articoli news (griglia + slider)
- `OrganigramPersonCard` — organigramma Chi siamo
