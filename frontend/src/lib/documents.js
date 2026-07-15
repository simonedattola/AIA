/** Sezioni documenti — ordine e raggruppamento (configurabile da admin). */

export const DEFAULT_DOCUMENT_SECTIONS = [
  "Regolamenti del giuoco del calcio",
  "Regolamenti A.I.A.",
  "Documentazione amministrativa CRA/CPA",
  "Documentazione amministrativa Sezioni",
  "Assemblea Sezionale Elettiva",
  "Assemblea Sezionale Ordinaria",
  "Assemblea Regionale Elettiva",
  "Assemblea Generale Elettiva",
];

/** @deprecated usa DEFAULT_DOCUMENT_SECTIONS */
export const DOCUMENT_SECTIONS = DEFAULT_DOCUMENT_SECTIONS;

const LEGACY_CATEGORY_MAP = {
  regolamento: "Regolamenti del giuoco del calcio",
  modulistica: "Documentazione amministrativa Sezioni",
  tecnica: "Documentazione amministrativa Sezioni",
  comunicazioni: "Documentazione amministrativa CRA/CPA",
  "Download sezionale": "Documentazione amministrativa Sezioni",
};

function sectionSortIndex(title, sectionOrder) {
  const order = sectionOrder?.length ? sectionOrder : DEFAULT_DOCUMENT_SECTIONS;
  const i = order.indexOf(title);
  return i === -1 ? 9999 : i;
}

/** Sezione/categoria visualizzata per un documento. */
export function documentSection(doc, sectionOrder = DEFAULT_DOCUMENT_SECTIONS) {
  const cat = (doc?.category || "").trim();
  if (cat && (sectionOrder.includes(cat) || !LEGACY_CATEGORY_MAP[cat])) return cat;
  if (LEGACY_CATEGORY_MAP[cat]) return LEGACY_CATEGORY_MAP[cat];
  const sec = (doc?.section || "").trim();
  if (sec && (sectionOrder.includes(sec) || !LEGACY_CATEGORY_MAP[sec])) return sec;
  if (LEGACY_CATEGORY_MAP[sec]) return LEGACY_CATEGORY_MAP[sec];
  return sectionOrder[3] || DEFAULT_DOCUMENT_SECTIONS[3];
}

export function groupDocumentsBySection(documents = [], sectionOrder = DEFAULT_DOCUMENT_SECTIONS) {
  const map = new Map();
  for (const doc of documents) {
    const title = documentSection(doc, sectionOrder);
    if (!map.has(title)) map.set(title, []);
    map.get(title).push(doc);
  }

  return [...map.entries()]
    .map(([title, items]) => ({
      title,
      items: [...items].sort((a, b) => (a.sortOrder ?? 0) - (b.sortOrder ?? 0)),
      order: sectionSortIndex(title, sectionOrder),
    }))
    .sort((a, b) => a.order - b.order || a.title.localeCompare(b.title, "it"));
}

export function documentSubtitle(doc) {
  const desc = (doc?.description || "").trim();
  if (desc) return desc;
  return (doc?.fileSize || "").trim();
}
