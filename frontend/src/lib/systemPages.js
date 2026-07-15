/** Pagine di sistema — percorsi pubblici e raggruppamento admin. */

export const SYSTEM_ROUTES = {
  home: "/",
  "chi-siamo": "/chi-siamo",
  designazioni: "/designazioni",
  arbitri: "/arbitri",
  news: "/news",
  eventi: "/eventi",
  contatti: "/contatti",
  "diventa-arbitro": "/diventa-arbitro",
  "area-associati": "/area-associati/login",
  "arbitro-profilo": "/arbitri/esempio",
};

export const SYSTEM_SLUGS = new Set(Object.keys(SYSTEM_ROUTES));

/**
 * Pagine con intestazione navy compatta (campi pagina: eyebrow, heading, summary).
 * Non usano il blocco Hero in cima — eccezione: home e diventa-arbitro.
 */
export const COMPACT_HEADER_SLUGS = new Set([
  "chi-siamo",
  "designazioni",
  "arbitri",
  "news",
  "eventi",
  "contatti",
]);

/** Pagine con hero a tutta larghezza in cima (no banner compatto). */
export const FULL_BLEED_HERO_SLUGS = new Set(["home", "diventa-arbitro"]);

/** Non modificabili da Admin → Pagine (layout fisso). */
export const ADMIN_HIDDEN_PAGE_SLUGS = new Set(["area-associati", "arbitro-profilo"]);

export const SYSTEM_ORDER = Object.keys(SYSTEM_ROUTES).filter((s) => !ADMIN_HIDDEN_PAGE_SLUGS.has(s));

export function publicPathFor(slug) {
  return SYSTEM_ROUTES[slug] || `/p/${slug}`;
}

export function sortPages(items) {
  return [...items].sort((a, b) => {
    const ai = SYSTEM_ORDER.indexOf(a.slug);
    const bi = SYSTEM_ORDER.indexOf(b.slug);
    if (ai !== -1 || bi !== -1) {
      if (ai === -1) return 1;
      if (bi === -1) return -1;
      return ai - bi;
    }
    return (a.menuOrder ?? 100) - (b.menuOrder ?? 100) || (a.title || "").localeCompare(b.title || "");
  });
}
