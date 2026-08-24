export function formatDateIt(input, opts = {}) {
  const raw = typeof input === "string" ? input : input instanceof Date ? input : "";
  if (!raw) return "";
  const d = typeof raw === "string" ? new Date(raw) : raw;
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("it-IT", {
    day: "2-digit", month: opts.short ? "short" : "long", year: "numeric",
  });
}

export function formatDateShort(input) {
  if (!input) return "";
  const d = typeof input === "string" ? new Date(input) : input;
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("it-IT", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export function formatDateTimeIt(input) {
  if (!input) return "";
  const d = new Date(input);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("it-IT", {
    day: "2-digit", month: "long", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

/** Data evento + orario (HH:MM) in italiano. orarioFine opzionale. */
export function formatEventDateTimeIt(date, orario, orarioFine) {
  if (!date) return "";
  const d = new Date(`${String(date).slice(0, 10)}T12:00:00`);
  if (Number.isNaN(d.getTime())) return "";
  const datePart = d.toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
  const start = (orario || "09:00").slice(0, 5);
  const end = (orarioFine || "").slice(0, 5);
  if (end && end !== start) {
    return `${datePart} dalle ${start} alle ${end}`;
  }
  return `${datePart} alle ${start}`;
}

export function formatMonthYear(input) {
  if (!input) return "";
  const d = new Date(input);
  return d.toLocaleDateString("it-IT", { month: "long", year: "numeric" });
}

/** Preferenza contatto lead corso arbitri (valori API: email | phone). */
export function contactPreferenceLabel(pref, { lowercase = false } = {}) {
  if (pref === "phone") return lowercase ? "telefono" : "Telefono";
  if (pref === "email") return lowercase ? "email" : "Email";
  return pref || "—";
}

export function formatFileSize(bytes) {
  if (!bytes || bytes <= 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Nome Cognome in title case (es. MARIO ROSSI → Mario Rossi). */
export function formatPersonName(firstName, lastName, fullName) {
  const titleWord = (word) => {
    const w = String(word || "").trim();
    if (!w) return "";
    if (w.includes(" ")) return w.split(/\s+/).filter(Boolean).map(titleWord).join(" ");
    if (w.length === 1) return w.toUpperCase();
    if (w.includes("-")) return w.split("-").map(titleWord).join("-");
    return w.charAt(0).toUpperCase() + w.slice(1).toLowerCase();
  };
  if (fullName && !firstName && !lastName) {
    return String(fullName)
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .map(titleWord)
      .join(" ");
  }
  const parts = [titleWord(firstName), titleWord(lastName)].filter(Boolean);
  return parts.join(" ");
}
