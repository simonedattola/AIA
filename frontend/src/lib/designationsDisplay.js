import { asAdminText as asText } from "./safeText";

export function displayDesignationGara(d) {
  const home = asText(d?.matchHome);
  const away = asText(d?.matchAway);
  if (home && away) return `${home} - ${away}`;
  return asText(d?.matchLabel) || "—";
}

export function displayDesignationCampionato(d) {
  return asText(d?.championship || d?.category).trim() || "—";
}

export function displayDesignationGirone(d) {
  return asText(d?.girone).trim() || "—";
}

export function displayDesignationGiornata(d) {
  return asText(d?.matchDay).trim() || "—";
}

export function formatDesignationMeta(d) {
  const girone = asText(d?.girone);
  const matchDay = asText(d?.matchDay);
  return [
    displayDesignationCampionato(d),
    girone && `Gir. ${girone}`,
    matchDay && `G.${matchDay}`,
  ]
    .filter(Boolean)
    .join(" · ") || "—";
}

export function formatSeasonLabel(s) {
  const label = asText(s);
  if (!label || !label.includes("-")) return label || "Stagione";
  const [a, b] = label.split("-");
  return `${a}/${b}`;
}
