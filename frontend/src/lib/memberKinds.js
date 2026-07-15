/** Allineato a backend/app/member_kinds.py */
export const ASSOCIATI_KINDS = new Set(["associato", "tutor"]);
export const OBSERVER_KINDS = new Set(["oa", "ot", "osservatore"]);

export function isAssociatoKind(kind) {
  return ASSOCIATI_KINDS.has(kind || "associato");
}

export function isObserverKind(kind) {
  return OBSERVER_KINDS.has((kind || "").toLowerCase());
}

export function memberKindLabel(kind) {
  const k = (kind || "").toLowerCase();
  if (k === "oa" || k === "osservatore") return "OA";
  if (k === "ot") return "OT";
  return "";
}

export function memberKindSubtitle(kind) {
  const k = (kind || "").toLowerCase();
  if (k === "oa" || k === "osservatore") return "Osservatore Arbitrale";
  if (k === "ot") return "Organo Tecnico";
  return "";
}
