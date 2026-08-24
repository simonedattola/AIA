/**
 * Values from API/Mongo must never be passed as React children if they are objects.
 * Pydantic/FastAPI errors look like { type, loc, msg, input, ctx } and trigger React #31.
 */
export function asAdminText(value, fallback = "") {
  if (value == null || value === false) return fallback;
  const t = typeof value;
  if (t === "string") return value;
  if (t === "number" && Number.isFinite(value)) return String(value);
  if (t === "boolean") return value ? "true" : fallback;
  if (t !== "object") return fallback;
  if (typeof value.msg === "string" && value.msg.trim()) return value.msg;
  if (typeof value.message === "string" && value.message.trim()) return value.message;
  if (typeof value.title === "string" && value.title.trim()) return value.title;
  if (typeof value.label === "string" && value.label.trim()) return value.label;
  return fallback;
}

export function asAdminCount(value) {
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : 0;
}
