export const MEMBER_ROLES = [
  { value: "arbitro", label: "Arbitro" },
  { value: "assistente", label: "Assistente" },
  { value: "consiglio_direttivo", label: "Consiglio Direttivo" },
  { value: "osservatore", label: "Osservatore" },
];

export const ROLE_FILTERS = [
  { value: "", label: "Tutti" },
  ...MEMBER_ROLES,
];

const VALID_ROLES = new Set(["arbitro", "assistente", "consiglio_direttivo", "osservatore"]);

function inferMemberRole(m) {
  const kind = (m.kind || "").toLowerCase();
  const role = (m.role || "").toLowerCase();
  if (kind === "oa" || kind === "ot" || kind === "osservatore" || role.includes("osservatore")) {
    return { memberRole: "osservatore", observerType: kind === "ot" ? "ot" : "oa" };
  }
  if (role.includes("assistente") || kind === "tutor") {
    return { memberRole: "assistente" };
  }
  if (role.includes("consiglio") || role.includes("presidente") || role.includes("segretario")) {
    return { memberRole: "consiglio_direttivo" };
  }
  return { memberRole: "arbitro" };
}

export function normalizeMember(m) {
  if (!m) return m;
  const out = { ...m };
  let role = (out.memberRole || "").trim().toLowerCase();
  if (!VALID_ROLES.has(role)) {
    const inferred = inferMemberRole(out);
    Object.assign(out, inferred);
    role = out.memberRole;
  } else {
    out.memberRole = role;
  }
  if (out.memberRole === "osservatore" && !out.observerType) {
    out.observerType = (out.kind || "").toLowerCase() === "ot" ? "ot" : "oa";
  }
  if (!out.bio && out.bioHtml) {
    out.bio = out.bioHtml.replace(/<[^>]+>/g, "").trim();
  }
  return out;
}

export function hasDesignations(memberRole) {
  return memberRole === "arbitro" || memberRole === "assistente";
}

function isArbitroBenemerito(m) {
  const code = String(m?.role || "").trim().toUpperCase();
  if (code === "AB") return true;
  return String(m?.category || "").toLowerCase().includes("benemerito");
}

export function memberRoleLabel(m) {
  if (isArbitroBenemerito(m)) {
    const board = (m?.boardTitle || "").trim();
    if (board && !/^arbitro\s+benemerito$/i.test(board)) {
      return `Arbitro Benemerito · ${board}`;
    }
    return "Arbitro Benemerito";
  }
  const r = m?.memberRole;
  const board = (m?.boardTitle || "").trim();
  const code = String(m?.role || "").trim().toUpperCase();
  if (r === "arbitro") {
    const base = code === "AE" ? "Arbitro Effettivo" : code === "AA" ? "Arbitro Aspirante" : "Arbitro";
    return board ? `${base} · ${board}` : base;
  }
  if (r === "assistente") return board ? `Assistente Arbitrale · ${board}` : "Assistente Arbitrale";
  if (r === "consiglio_direttivo") return board || "Consiglio Direttivo";
  if (r === "osservatore") {
    const base = m?.observerType === "ot" ? "OT · Organo Tecnico" : "OA · Osservatore Arbitrale";
    return board ? `${base} · ${board}` : base;
  }
  return m?.role || "";
}

export function profileBackPath(memberRole, member) {
  if (memberRole === "osservatore") return "/osservatori";
  const board = (member?.boardTitle || "").trim();
  if (board && !/^arbitro\s+benemerito$/i.test(board)) return "/chi-siamo";
  if (memberRole === "consiglio_direttivo") return "/chi-siamo";
  return "/arbitri";
}
