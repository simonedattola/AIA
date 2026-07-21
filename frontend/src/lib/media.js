/** Turn /api/uploads/... paths into full backend URLs for <img src>. */
const BACKEND_URL = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "");
const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "0.0.0.0", "[::1]"]);

function localUploadPath(absoluteUrl) {
  try {
    const parsed = new URL(absoluteUrl);
    if (!LOCAL_HOSTS.has(parsed.hostname.toLowerCase())) return null;
    const path = parsed.pathname || "";
    if (path.startsWith("/api/uploads/") || path.startsWith("/uploads/")) {
      return path.startsWith("/api/") ? path : `/api${path}`;
    }
  } catch {
    /* ignore invalid URLs */
  }
  return null;
}

export function mediaUrl(url) {
  if (!url || typeof url !== "string") return "";
  const u = url.trim();
  const fromLocal = localUploadPath(u);
  if (fromLocal) {
    return BACKEND_URL ? `${BACKEND_URL}${fromLocal}` : fromLocal;
  }
  if (u.startsWith("http://") || u.startsWith("https://")) return u;
  if (!BACKEND_URL) return u;
  if (u.startsWith("/api/") || u.startsWith("/uploads/")) {
    const path = u.startsWith("/api/") ? u : `/api${u.startsWith("/") ? u : `/${u}`}`;
    return `${BACKEND_URL}${path}`;
  }
  if (u.startsWith("/")) return `${BACKEND_URL}${u}`;
  return u;
}
