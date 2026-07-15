import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";

export function cn(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

export function formatDate(date: Date | string, pattern = "dd MMM yyyy") {
  const d = typeof date === "string" ? parseISO(date) : date;
  return format(d, pattern, { locale: it });
}

export function formatDateTime(date: Date | string) {
  return formatDate(date, "dd MMM yyyy HH:mm");
}

export function currentSeason(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  if (month >= 6) return `${year}-${String(year + 1).slice(-2)}`;
  return `${year - 1}-${String(year).slice(-2)}`;
}

export function seasonFromDate(date: Date): string {
  const year = date.getFullYear();
  const month = date.getMonth();
  if (month >= 6) return `${year}-${String(year + 1).slice(-2)}`;
  return `${year - 1}-${String(year).slice(-2)}`;
}
