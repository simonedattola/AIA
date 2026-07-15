export function displayDesignationGara(d) {
  if (d.matchHome && d.matchAway) return `${d.matchHome} - ${d.matchAway}`;
  return d.matchLabel || "—";
}

export function displayDesignationCampionato(d) {
  return (d.championship || d.category || "").trim() || "—";
}

export function displayDesignationGirone(d) {
  return (d.girone || "").trim() || "—";
}

export function displayDesignationGiornata(d) {
  return (d.matchDay || "").trim() || "—";
}

export function formatDesignationMeta(d) {
  return [
    displayDesignationCampionato(d),
    d.girone && `Gir. ${d.girone}`,
    d.matchDay && `G.${d.matchDay}`,
  ]
    .filter(Boolean)
    .join(" · ") || "—";
}

export function formatSeasonLabel(s) {
  if (!s || !s.includes("-")) return s || "Stagione";
  const [a, b] = s.split("-");
  return `${a}/${b}`;
}
