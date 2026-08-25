"""Sitemap.xml e robots.txt dinamici per SEO."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable
from xml.sax.saxutils import escape

from .mailer import portal_frontend_url
from .page_nav import SYSTEM_PAGE_HREFS, page_href

# Pagine di sistema escluse dalla sitemap (auth / template interni)
SITEMAP_EXCLUDED_SYSTEM_SLUGS = frozenset({"area-associati", "arbitro-profilo"})

# Priorità relative (home più alta)
PRIORITY_HOME = "1.0"
PRIORITY_SECTION = "0.8"
PRIORITY_ARTICLE = "0.7"
PRIORITY_MEMBER = "0.6"
PRIORITY_CUSTOM = "0.5"

CHANGEFREQ_HOME = "daily"
CHANGEFREQ_SECTION = "weekly"
CHANGEFREQ_ARTICLE = "weekly"
CHANGEFREQ_MEMBER = "monthly"
CHANGEFREQ_CUSTOM = "monthly"


def _iso_date(value: str | None) -> str | None:
    """Normalizza timestamp ISO a YYYY-MM-DD per lastmod."""
    if not value or not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        # Accetta ISO con/senza timezone
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        return dt.date().isoformat()
    except ValueError:
        if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
            return raw[:10]
    return None


def _url_entry(loc: str, lastmod: str | None, changefreq: str, priority: str) -> str:
    parts = [f"  <url>", f"    <loc>{escape(loc)}</loc>"]
    if lastmod:
        parts.append(f"    <lastmod>{escape(lastmod)}</lastmod>")
    parts.append(f"    <changefreq>{changefreq}</changefreq>")
    parts.append(f"    <priority>{priority}</priority>")
    parts.append("  </url>")
    return "\n".join(parts)


def absolute_url(path: str, base: str | None = None) -> str:
    root = (base or portal_frontend_url()).rstrip("/")
    if not path or path == "/":
        return f"{root}/"
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{root}{path}"


async def collect_sitemap_urls(db) -> list[dict]:
    """Raccoglie URL pubblici da pagine, articoli e profili associati."""
    today = datetime.now(timezone.utc).date().isoformat()
    urls: list[dict] = []
    seen: set[str] = set()

    def add(path: str, *, lastmod: str | None, changefreq: str, priority: str):
        loc = absolute_url(path)
        if loc in seen:
            return
        seen.add(loc)
        urls.append(
            {
                "loc": loc,
                "lastmod": lastmod or today,
                "changefreq": changefreq,
                "priority": priority,
            }
        )

    # Pagine CMS pubblicate (sistema + custom)
    pages = await db.pages.find(
        {"status": "published"},
        {"_id": 0, "slug": 1, "updatedAt": 1},
    ).to_list(500)

    for slug, href in SYSTEM_PAGE_HREFS.items():
        if slug in SITEMAP_EXCLUDED_SYSTEM_SLUGS:
            continue
        # Preferisci lastmod dal DB se la pagina esiste
        lastmod = None
        for p in pages:
            if p.get("slug") == slug:
                lastmod = _iso_date(p.get("updatedAt"))
                break
        add(
            href,
            lastmod=lastmod,
            changefreq=CHANGEFREQ_HOME if slug == "home" else CHANGEFREQ_SECTION,
            priority=PRIORITY_HOME if slug == "home" else PRIORITY_SECTION,
        )

    for p in pages:
        slug = (p.get("slug") or "").strip()
        if (
            not slug
            or slug in SYSTEM_PAGE_HREFS
            or slug in SITEMAP_EXCLUDED_SYSTEM_SLUGS
        ):
            continue
        add(
            page_href(slug),
            lastmod=_iso_date(p.get("updatedAt")),
            changefreq=CHANGEFREQ_CUSTOM,
            priority=PRIORITY_CUSTOM,
        )

    # Articoli pubblicati (non solo area associati)
    articles = await db.articles.find(
        {"status": "published", "portalOnly": {"$ne": True}},
        {"_id": 0, "slug": 1, "updatedAt": 1, "publishedAt": 1},
    ).to_list(2000)
    for art in articles:
        slug = (art.get("slug") or "").strip()
        if not slug:
            continue
        add(
            f"/news/{slug}",
            lastmod=_iso_date(art.get("updatedAt") or art.get("publishedAt")),
            changefreq=CHANGEFREQ_ARTICLE,
            priority=PRIORITY_ARTICLE,
        )

    # Profili pubblici associati
    members = await db.members.find(
        {"slug": {"$exists": True, "$nin": ["", None]}},
        {"_id": 0, "slug": 1, "updatedAt": 1},
    ).to_list(2000)
    for m in members:
        slug = (m.get("slug") or "").strip()
        if not slug:
            continue
        add(
            f"/arbitri/{slug}",
            lastmod=_iso_date(m.get("updatedAt")),
            changefreq=CHANGEFREQ_MEMBER,
            priority=PRIORITY_MEMBER,
        )

    return urls


def render_sitemap_xml(urls: Iterable[dict]) -> str:
    entries = [
        _url_entry(
            u["loc"],
            u.get("lastmod"),
            u.get("changefreq") or CHANGEFREQ_SECTION,
            u.get("priority") or PRIORITY_SECTION,
        )
        for u in urls
    ]
    body = "\n".join(entries)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n"
    )


def render_robots_txt(base: str | None = None) -> str:
    root = (base or portal_frontend_url()).rstrip("/")
    sitemap_loc = f"{root}/sitemap.xml"
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "Disallow: /amministrazione\n"
        "Disallow: /amministrazione/\n"
        "Disallow: /area-associati\n"
        "Disallow: /area-associati/\n"
        "Disallow: /admin\n"
        "Disallow: /admin/\n"
        "Disallow: /api/\n"
        "\n"
        f"Sitemap: {sitemap_loc}\n"
    )
