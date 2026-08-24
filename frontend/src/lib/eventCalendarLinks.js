/** Link Google Calendar + download .ics (Apple / Outlook / Google). */

const DEFAULT_DURATION_MS = 2 * 60 * 60 * 1000;

function pad(n) {
  return String(n).padStart(2, "0");
}

/** Parse event.date (YYYY-MM-DD) + orario (HH:MM) as Europe/Rome wall time → Date (local interpretation via offset). */
export function eventStartDate(event) {
  const date = String(event?.date || "").slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return null;
  let orario = String(event?.orario || "09:00").trim();
  const m = orario.match(/^(\d{1,2}):(\d{2})$/);
  if (!m) orario = "09:00";
  else {
    const h = Number(m[1]);
    const min = Number(m[2]);
    if (h > 23 || min > 59) orario = "09:00";
    else orario = `${pad(h)}:${pad(min)}`;
  }
  // Treat as Rome local by appending offset is fragile with DST; use Intl-free approach:
  // construct as UTC components labeled Rome via temporal-less method: Date from ISO with explicit offset approximation.
  // Better: format parts and use Date.UTC then adjust with Rome offset at that date.
  const [y, mo, d] = date.split("-").map(Number);
  const [hh, mm] = orario.split(":").map(Number);
  // Guess Rome offset (CET +1 / CEST +2) for that calendar day at noon
  const probe = new Date(Date.UTC(y, mo - 1, d, 12, 0, 0));
  const romeParts = new Intl.DateTimeFormat("en-US", {
    timeZone: "Europe/Rome",
    timeZoneName: "shortOffset",
  }).formatToParts(probe);
  const tzName = romeParts.find((p) => p.type === "timeZoneName")?.value || "GMT+1";
  const off = tzName.match(/GMT([+-])(\d{1,2})(?::?(\d{2}))?/i);
  let offsetMin = 60;
  if (off) {
    const sign = off[1] === "-" ? -1 : 1;
    offsetMin = sign * (Number(off[2]) * 60 + Number(off[3] || 0));
  }
  // Rome local = UTC + offset → UTC = local - offset
  const utcMs = Date.UTC(y, mo - 1, d, hh, mm, 0) - offsetMin * 60 * 1000;
  return new Date(utcMs);
}

function toGoogleUtcStamp(date) {
  return (
    date.getUTCFullYear() +
    pad(date.getUTCMonth() + 1) +
    pad(date.getUTCDate()) +
    "T" +
    pad(date.getUTCHours()) +
    pad(date.getUTCMinutes()) +
    pad(date.getUTCSeconds()) +
    "Z"
  );
}

function toIcsLocalStamp(date) {
  // Format in Europe/Rome wall clock
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Rome",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(date);
  const get = (t) => parts.find((p) => p.type === t)?.value || "00";
  return `${get("year")}${get("month")}${get("day")}T${get("hour")}${get("minute")}${get("second")}`;
}

function icsEscape(text) {
  return String(text || "")
    .replace(/\\/g, "\\\\")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,")
    .replace(/\r\n|\n|\r/g, "\\n");
}

export function googleCalendarUrl(event) {
  const start = eventStartDate(event);
  if (!start) return "";
  const end = new Date(start.getTime() + DEFAULT_DURATION_MS);
  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: (event.titolo || "Evento AIA Legnano").trim(),
    dates: `${toGoogleUtcStamp(start)}/${toGoogleUtcStamp(end)}`,
    ctz: "Europe/Rome",
  });
  if (event.descrizione) params.set("details", String(event.descrizione).trim());
  if (event.luogo) params.set("location", String(event.luogo).trim());
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

export function buildIcsContent(event) {
  const start = eventStartDate(event);
  if (!start) return "";
  const end = new Date(start.getTime() + DEFAULT_DURATION_MS);
  const uid = `aia-legnano-event-${event.id || "evento"}@aia-legnano.it`;
  const stamp = toGoogleUtcStamp(new Date());
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//AIA Legnano//Eventi//IT",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "BEGIN:VEVENT",
    `UID:${uid}`,
    `DTSTAMP:${stamp}`,
    `DTSTART;TZID=Europe/Rome:${toIcsLocalStamp(start)}`,
    `DTEND;TZID=Europe/Rome:${toIcsLocalStamp(end)}`,
    `SUMMARY:${icsEscape(event.titolo || "Evento AIA Legnano")}`,
  ];
  if (event.luogo) lines.push(`LOCATION:${icsEscape(event.luogo)}`);
  if (event.descrizione) lines.push(`DESCRIPTION:${icsEscape(event.descrizione)}`);
  lines.push("STATUS:CONFIRMED", "END:VEVENT", "END:VCALENDAR");
  return `${lines.join("\r\n")}\r\n`;
}

export function icsFilename(event) {
  const title = String(event.titolo || "evento")
    .trim()
    .replace(/[^\w\-]+/g, "-")
    .replace(/-{2,}/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 40) || "evento";
  const date = String(event.date || "").slice(0, 10).replace(/-/g, "");
  return `aia-legnano-${title}-${date || "data"}.ics`;
}

/** Scarica .ics nel browser (Apple Calendar / Outlook / Google). */
export function downloadEventIcs(event) {
  const content = buildIcsContent(event);
  if (!content) return false;
  const blob = new Blob([content], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = icsFilename(event);
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  return true;
}
