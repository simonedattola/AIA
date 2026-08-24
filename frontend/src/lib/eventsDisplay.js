export const TYPE_LABEL = {
  rto: "RTO",
  riunione: "Riunione tecnica",
  allenamento: "Allenamento",
  corso: "Corso arbitri",
  sociale: "Evento sociale",
  raduno: "Raduno",
};

export const TYPE_COLOR = {
  rto: "bg-violet-50 text-violet-800",
  riunione: "bg-navy-50 text-navy-700",
  allenamento: "bg-emerald-50 text-emerald-700",
  corso: "bg-gold-100 text-gold-700",
  sociale: "bg-pink-50 text-pink-700",
  raduno: "bg-indigo-50 text-indigo-700",
};

export const MONTHS_SHORT = ["GEN", "FEB", "MAR", "APR", "MAG", "GIU", "LUG", "AGO", "SET", "OTT", "NOV", "DIC"];

export const MONTHS_IT = [
  "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
  "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
];

export const WEEKDAYS_IT = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"];

export function eventDateKey(dateStr) {
  return String(typeof dateStr === "string" ? dateStr : "").slice(0, 10);
}

export function todayKey() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function isUpcomingEvent(event) {
  return eventDateKey(event?.date) >= todayKey();
}

export function groupEventsByDate(events) {
  const map = {};
  for (const ev of events || []) {
    const key = eventDateKey(ev.date);
    if (!key) continue;
    if (!map[key]) map[key] = [];
    map[key].push(ev);
  }
  for (const key of Object.keys(map)) {
    map[key].sort((a, b) => (a.titolo || "").localeCompare(b.titolo || "", "it"));
  }
  return map;
}

export function ymdKey(year, monthIndex, day) {
  return `${year}-${String(monthIndex + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

export function buildMonthGrid(year, monthIndex) {
  const first = new Date(year, monthIndex, 1);
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
  const startPad = (first.getDay() + 6) % 7;
  const cells = [];
  for (let i = 0; i < startPad; i += 1) cells.push(null);
  for (let d = 1; d <= daysInMonth; d += 1) cells.push(d);
  while (cells.length % 7 !== 0) cells.push(null);
  return cells;
}
