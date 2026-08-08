export const AIA_QUALIFICHE = [
  { value: "", label: "—" },
  { value: "AE", label: "AE — Arbitro Effettivo" },
  { value: "AA", label: "AA — Assistente Arbitrale" },
  { value: "AB", label: "AB — Arbitro Benemerito" },
  { value: "AFR", label: "AFR — Arbitro Fuori Ruolo" },
  { value: "OA", label: "OA — Osservatore Arbitrale" },
  { value: "OT", label: "OT — Organo Tecnico" },
];

export const ORGANIGRAMMA_KINDS = [
  { value: "", label: "—" },
  { value: "cds", label: "CDS — Consiglio Direttivo Sezionale" },
  { value: "collaboratore", label: "Collaboratore" },
  { value: "ors", label: "ORS — Organo di Revisione Sezionale" },
];

/** @deprecated prefer AIA_QUALIFICHE + ORGANIGRAMMA_KINDS */
export const MEMBER_ROLES = [
  { value: "arbitro", label: "Arbitro" },
  { value: "assistente", label: "Assistente Arbitrale" },
  { value: "consiglio_direttivo", label: "Consiglio Direttivo" },
  { value: "osservatore", label: "Osservatore" },
];

export const ROLE_FILTERS = [
  { value: "", label: "Tutti" },
  { value: "AE", label: "AE" },
  { value: "AA", label: "AA" },
  { value: "AB", label: "AB" },
  { value: "AFR", label: "AFR" },
  { value: "OA", label: "OA" },
  { value: "OT", label: "OT" },
  { value: "cds", label: "CDS" },
  { value: "collaboratore", label: "Collaboratori" },
  { value: "ors", label: "ORS" },
];

const VALID_ROLES = new Set(["arbitro", "assistente", "consiglio_direttivo", "osservatore"]);
const AIA_TO_ROLE = {
  AE: "arbitro",
  AA: "assistente",
  AB: "arbitro",
  AFR: "arbitro",
  OA: "osservatore",
  OT: "osservatore",
};
const ORG_KINDS = new Set(["cds", "collaboratore", "ors"]);

function aiaCodeOf(m) {
  const code = String(m?.role || "").trim().toUpperCase();
  return AIA_TO_ROLE[code] ? code : "";
}

export function canHaveMaxCategory(m) {
  const code = aiaCodeOf(m);
  return code === "AE" || code === "AA";
}

export function defaultPortalPassword(firstName, lastName) {
  const norm = (s) =>
    String(s || "")
      .trim()
      .toLowerCase()
      .replace(/à/g, "a")
      .replace(/[èé]/g, "e")
      .replace(/ì/g, "i")
      .replace(/ò/g, "o")
      .replace(/ù/g, "u");
  return `${norm(firstName)}.${norm(lastName)}`;
}

export function seniorityYears(yearStart, now = new Date().getFullYear()) {
  const y = Number(yearStart);
  if (!y || y < 1900 || y > now + 1) return null;
  return Math.max(0, now - y);
}

export function yearStartFromSeniority(years, now = new Date().getFullYear()) {
  const n = Number(years);
  if (years === "" || years == null || Number.isNaN(n) || n < 0) return null;
  return now - Math.floor(n);
}

function inferOrganigrammaKind(m) {
  const explicit = String(m.organigrammaKind || "").trim().toLowerCase();
  if (ORG_KINDS.has(explicit)) return explicit;
  const bt = String(m.boardTitle || "").trim();
  if (!bt || /^arbitro\s+benemerito$/i.test(bt)) {
    if (String(m.memberRole || "").toLowerCase() === "consiglio_direttivo") return "cds";
    return "";
  }
  const low = bt.toLowerCase();
  if (low.includes("revisione") || low.includes("revisori")) return "ors";
  if (/^\s*collaboratore\b/.test(low) || low.includes("collaboratore —") || low.includes("collaboratore -")) {
    return "collaboratore";
  }
  if (
    low.includes("consigliere") ||
    /vice\s*-?\s*presidente|vicepresidente/.test(low) ||
    low.includes("presidente di sezione") ||
    /^\s*presidente\b/.test(low) ||
    low.includes("segretario") ||
    low.includes("cassiere") ||
    String(m.memberRole || "").toLowerCase() === "consiglio_direttivo"
  ) {
    return "cds";
  }
  if (bt) return "collaboratore";
  return "";
}

export function isSectionPresident(m) {
  const kind = String(m?.organigrammaKind || "").trim().toLowerCase() || inferOrganigrammaKind(m || {});
  const bt = String(m?.boardTitle || "").trim();
  if (kind && kind !== "cds") return false;
  if (!bt) return false;
  const low = bt.toLowerCase();
  if (low.includes("revisione") || low.includes("revisori")) return false;
  if (/vice\s*-?\s*presidente|vicepresidente/i.test(bt)) return false;
  return /\bpresidente\b/i.test(bt);
}

function inferMemberRole(m) {
  const code = aiaCodeOf(m);
  if (code) {
    return {
      memberRole: AIA_TO_ROLE[code],
      observerType: code === "OT" ? "ot" : code === "OA" ? "oa" : undefined,
    };
  }
  const kind = (m.kind || "").toLowerCase();
  const role = (m.role || "").toLowerCase();
  if (kind === "oa" || kind === "ot" || kind === "osservatore" || role.includes("osservatore")) {
    return { memberRole: "osservatore", observerType: kind === "ot" ? "ot" : "oa" };
  }
  if (String(m.role || "").trim().toUpperCase() === "AA" || role.includes("assistente") || kind === "tutor") {
    return { memberRole: "assistente" };
  }
  const org = inferOrganigrammaKind(m);
  if (org === "cds") return { memberRole: "consiglio_direttivo" };
  return { memberRole: "arbitro" };
}

export function normalizeMember(m) {
  if (!m) return m;
  const out = { ...m };
  const code = aiaCodeOf(out);
  if (code) out.role = code;
  out.organigrammaKind = inferOrganigrammaKind(out);

  let role = (out.memberRole || "").trim().toLowerCase();
  if (code || !VALID_ROLES.has(role)) {
    const inferred = inferMemberRole(out);
    Object.assign(out, inferred);
    role = out.memberRole;
  } else {
    out.memberRole = role;
  }
  if (out.memberRole === "osservatore" && !out.observerType) {
    out.observerType = code === "OT" || (out.kind || "").toLowerCase() === "ot" ? "ot" : "oa";
  }
  if (out.memberRole !== "osservatore") out.observerType = "";
  out.isPresident = isSectionPresident(out);
  if (!canHaveMaxCategory(out)) out.category = "";
  if (!out.bio && out.bioHtml) {
    out.bio = out.bioHtml.replace(/<[^>]+>/g, "").trim();
  }
  if (!out.portalPassword) {
    out.portalPassword = defaultPortalPassword(out.firstName, out.lastName);
  }
  return out;
}

export function hasDesignations(memberRole) {
  return memberRole === "arbitro" || memberRole === "assistente";
}

function isArbitroBenemerito(m) {
  return aiaCodeOf(m) === "AB" || String(m?.category || "").toLowerCase().includes("benemerito");
}

export function memberRoleLabel(m) {
  const board = (m?.boardTitle || "").trim();
  const org = (m?.organigrammaKind || "").trim().toLowerCase();
  const orgLabel =
    org === "cds" ? "CDS" : org === "collaboratore" ? "Collaboratore" : org === "ors" ? "ORS" : "";
  const code = aiaCodeOf(m);

  let base = "";
  if (isArbitroBenemerito(m) || code === "AB") base = "Arbitro Benemerito";
  else if (code === "AA" || m?.memberRole === "assistente") base = "Assistente Arbitrale";
  else if (code === "AE") base = "Arbitro Effettivo";
  else if (code === "AFR") base = "Arbitro Fuori Ruolo";
  else if (code === "OA" || (m?.memberRole === "osservatore" && m?.observerType !== "ot")) base = "OA";
  else if (code === "OT" || m?.observerType === "ot") base = "OT";
  else if (m?.memberRole === "consiglio_direttivo") base = orgLabel || "CDS";
  else if (m?.memberRole === "arbitro") base = "Arbitro";
  else base = m?.role || "";

  const extras = [];
  if (orgLabel && !base.includes(orgLabel) && m?.memberRole !== "consiglio_direttivo") extras.push(orgLabel);
  if (board) extras.push(board);
  if (extras.length) return `${base} · ${extras.join(" · ")}`;
  return base || "";
}

export function profileBackPath(memberRole, member) {
  if (memberRole === "osservatore") return "/osservatori";
  const org = (member?.organigrammaKind || "").trim().toLowerCase();
  if (ORG_KINDS.has(org)) return "/chi-siamo";
  const board = (member?.boardTitle || "").trim();
  if (board && !/^arbitro\s+benemerito$/i.test(board)) return "/chi-siamo";
  if (memberRole === "consiglio_direttivo") return "/chi-siamo";
  return "/arbitri";
}

export function matchesRoleFilter(m, filter) {
  if (!filter) return true;
  const code = aiaCodeOf(m);
  const org = (m.organigrammaKind || "").toLowerCase();
  if (["AE", "AA", "AB", "AFR", "OA", "OT"].includes(filter)) return code === filter;
  if (ORG_KINDS.has(filter)) return org === filter;
  return (m.memberRole || "") === filter;
}
