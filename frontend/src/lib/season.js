import { formatSeasonLabel } from "./designationsDisplay";

/** Stagione calcistica corrente (1 ago – 31 lug), es. 2025-26 */
export function currentSeasonLabel(ref = new Date()) {
  const y = ref.getFullYear();
  const m = ref.getMonth() + 1;
  if (m >= 8) return `${y}-${String(y + 1).slice(-2)}`;
  return `${y - 1}-${String(y).slice(-2)}`;
}

export function currentSeasonLabelIt(ref = new Date()) {
  return formatSeasonLabel(currentSeasonLabel(ref));
}

export function seasonRangeDescription(ref = new Date()) {
  return `stagione ${currentSeasonLabelIt(ref)} (1 agosto – 31 luglio)`;
}
