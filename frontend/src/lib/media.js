/** Turn /api/uploads/... paths into full backend URLs for <img src>. */
const BACKEND_URL = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "");

export function mediaUrl(url) {
  if (!url || typeof url !== "string") return "";
  const u = url.trim();
  if (u.startsWith("http://") || u.startsWith("https://")) return u;
  if (!BACKEND_URL) return u;
  if (u.startsWith("/api/") || u.startsWith("/uploads/")) {
    const path = u.startsWith("/api/") ? u : `/api${u.startsWith("/") ? u : `/${u}`}`;
    return `${BACKEND_URL}${path}`;
  }
  if (u.startsWith("/")) return `${BACKEND_URL}${u}`;
  return u;
}
