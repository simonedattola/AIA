export function formatIgCount(n) {
  if (n == null || Number.isNaN(Number(n))) return null;
  const num = Number(n);
  if (num >= 1_000_000) {
    const v = num / 1_000_000;
    return `${v >= 10 ? Math.round(v) : v.toFixed(1).replace(/\.0$/, "")}M`;
  }
  if (num >= 10_000) {
    const v = num / 1_000;
    return `${v >= 100 ? Math.round(v) : v.toFixed(1).replace(/\.0$/, "")}K`;
  }
  if (num >= 1_000) {
    const v = num / 1_000;
    return `${v.toFixed(1).replace(/\.0$/, "")}K`;
  }
  return String(num);
}
