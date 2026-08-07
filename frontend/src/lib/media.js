/** Turn /api/uploads/... paths into usable <img src> URLs. */
const BACKEND_URL = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "");

/** Absolute local backend hosts that break on phone/tunnel when the SPA is same-origin proxied. */
const LOCAL_BACKEND_RE = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?/i;

/**
 * Resolve media URLs for the browser.
 * With empty REACT_APP_BACKEND_URL, keep paths same-origin (`/api/uploads/...`)
 * so Cloudflare tunnels / mobile previews can load images via the CRA proxy.
 */
export function mediaUrl(url) {
  if (!url || typeof url !== "string") return "";
  let u = url.trim();
  if (!u) return "";

  if (!BACKEND_URL && LOCAL_BACKEND_RE.test(u)) {
    u = u.replace(LOCAL_BACKEND_RE, "");
    if (!u.startsWith("/")) u = `/${u}`;
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
