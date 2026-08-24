/** Titolo scheda browser: «Pagina · AIA Legnano». */

export const SITE_BRAND = "AIA Legnano";

/** Titoli fissi per slug CMS di sistema (indipendenti dal titolo in DB). */
export const DOCUMENT_TITLE_BY_SLUG = {
  home: "Home",
  arbitri: "Arbitri",
  "chi-siamo": "Chi siamo",
  designazioni: "Designazioni",
  osservatori: "Osservatori",
  news: "News",
  eventi: "Eventi",
  contatti: "Contatti",
  "diventa-arbitro": "Diventa arbitro",
};

/**
 * Formatta il segmento pagina nel titolo scheda.
 * Es. "Home" → "Home · AIA Legnano"
 */
export function formatDocumentTitle(segment) {
  const raw = String(segment || "").trim();
  if (!raw) return SITE_BRAND;

  const cleaned = raw
    .replace(/\s*[·|–—]\s*AIA\s+Legnano\b.*$/i, "")
    .replace(/\s+AIA\s+Legnano\s*$/i, "")
    .trim();

  if (!cleaned || /^AIA\s+Legnano$/i.test(cleaned)) return SITE_BRAND;
  if (cleaned.includes("AIA") && /legnano/i.test(cleaned)) return cleaned;
  return `${cleaned} · ${SITE_BRAND}`;
}

export function setDocumentTitle(segment) {
  if (typeof document === "undefined") return;
  document.title = formatDocumentTitle(segment);
}

function longestPrefixMatch(pathname, entries) {
  let best = null;
  let bestLen = -1;
  for (const [prefix, label] of entries) {
    if (pathname === prefix || pathname.startsWith(`${prefix}/`)) {
      if (prefix.length > bestLen) {
        best = label;
        bestLen = prefix.length;
      }
    }
  }
  return best;
}

/**
 * Titolo scheda dal path. Per route dinamiche restituisce un fallback
 * (il contenuto specifico lo aggiorna la pagina quando carica i dati).
 */
export function documentTitleSegmentForPath(pathname) {
  const path = (pathname || "/").replace(/\/+$/, "") || "/";

  if (path === "/") return DOCUMENT_TITLE_BY_SLUG.home;

  const publicExact = {
    "/chi-siamo": DOCUMENT_TITLE_BY_SLUG["chi-siamo"],
    "/designazioni": DOCUMENT_TITLE_BY_SLUG.designazioni,
    "/arbitri": DOCUMENT_TITLE_BY_SLUG.arbitri,
    "/osservatori": DOCUMENT_TITLE_BY_SLUG.osservatori,
    "/news": DOCUMENT_TITLE_BY_SLUG.news,
    "/eventi": DOCUMENT_TITLE_BY_SLUG.eventi,
    "/contatti": DOCUMENT_TITLE_BY_SLUG.contatti,
    "/diventa-arbitro": DOCUMENT_TITLE_BY_SLUG["diventa-arbitro"],
    "/area-associati/login": "Accesso area associati",
    "/amministrazione/login": "Accesso amministrazione",
  };
  if (publicExact[path]) return publicExact[path];

  if (path.startsWith("/arbitri/")) return "Arbitro";
  if (path.startsWith("/news/")) return "News";
  if (path.startsWith("/p/")) return "Pagina";

  const portalEntries = [
    ["/area-associati", "Dashboard"],
    ["/area-associati/comunicazioni-interne", "Comunicazioni interne"],
    ["/area-associati/calendario", "Calendario"],
    ["/area-associati/storico-arbitrale", "Storico arbitrale"],
    ["/area-associati/documenti", "Documenti"],
    ["/area-associati/utility", "Utility"],
    ["/area-associati/galleria", "Galleria"],
    ["/area-associati/premi-e-menzioni", "Premi e menzioni"],
    ["/area-associati/messaggi", "Messaggi"],
    ["/area-associati/profilo", "Profilo"],
  ];
  if (path.startsWith("/area-associati")) {
    return longestPrefixMatch(path, portalEntries) || "Area associati";
  }

  const adminEntries = [
    ["/amministrazione", "Dashboard"],
    ["/amministrazione/anagrafica", "Anagrafica"],
    ["/amministrazione/designazioni", "Designazioni"],
    ["/amministrazione/comunicazioni-interne", "Comunicazioni interne"],
    ["/amministrazione/eventi", "Eventi"],
    ["/amministrazione/articoli", "Articoli"],
    ["/amministrazione/messaggi-sito", "Messaggi sito"],
    ["/amministrazione/candidature", "Candidature"],
    ["/amministrazione/galleria", "Galleria"],
    ["/amministrazione/testimonianze", "Testimonianze"],
    ["/amministrazione/documenti", "Documenti"],
    ["/amministrazione/utility", "Utility"],
    ["/amministrazione/pagine", "Pagine"],
    ["/amministrazione/impostazioni", "Impostazioni"],
  ];
  if (path.startsWith("/amministrazione")) {
    const label = longestPrefixMatch(path, adminEntries);
    if (path.match(/^\/amministrazione\/articoli\/[^/]+$/)) return "Modifica articolo";
    if (path.match(/^\/amministrazione\/pagine\/[^/]+$/)) return "Modifica pagina";
    if (path.match(/^\/amministrazione\/utility\/evento\/[^/]+$/)) return "Materiale RTO";
    return label || "Amministrazione";
  }

  return SITE_BRAND;
}
