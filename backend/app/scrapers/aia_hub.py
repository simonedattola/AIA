"""Scoperta hub da https://www.aia-figc.it/designazioni/ e crawl multi-hub."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx

from .aia_lombardia import (
    AiaLombardiaScraper,
    DEFAULT_HEADERS,
    ScrapeResult,
    _clean_text,
)

logger = logging.getLogger(__name__)

DESIGNAZIONI_ROOT = "https://www.aia-figc.it/designazioni/"

# Serie A — solo cognomi, escluso su richiesta sezione.
EXCLUDED_HUB_PATHS = frozenset({"/designazioni/can"})


@dataclass(frozen=True)
class DesignazioniHub:
    slug: str
    base_url: str
    label: str = ""


def _hub_slug_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/").lower()
    parts = path.split("/")
    if "designazioni" in parts:
        idx = parts.index("designazioni")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return "hub"


def is_excluded_hub_url(url: str) -> bool:
    path = urlparse(url).path.rstrip("/").lower()
    if not path.startswith("/designazioni/"):
        return True
    for ex in EXCLUDED_HUB_PATHS:
        if path == ex or path.startswith(ex + "/"):
            return True
    return False


def discover_designazioni_hubs(
    client: Optional[httpx.Client] = None,
    root_url: str = DESIGNAZIONI_ROOT,
) -> list[DesignazioniHub]:
    """Elenco hub regionali/nazionali dalla home designazioni."""
    own_client = client is None
    if own_client:
        client = httpx.Client(headers=DEFAULT_HEADERS, timeout=30.0)
    try:
        r = client.get(root_url, follow_redirects=True)
        r.raise_for_status()
        r.encoding = r.encoding or "utf-8"
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(r.text, "html.parser")
        hubs: dict[str, DesignazioniHub] = {}
        for a in soup.find_all("a", href=True):
            full = urljoin(root_url, a["href"])
            parsed = urlparse(full)
            if "designazioni" not in parsed.path.lower():
                continue
            if is_excluded_hub_url(full):
                continue
            path = parsed.path.rstrip("/")
            segs = [s for s in path.split("/") if s]
            if len(segs) < 2:
                continue
            if segs[-1] == "designazioni":
                continue
            slug = segs[-1].lower()
            base = f"{parsed.scheme}://{parsed.netloc}/designazioni/{slug}/"
            label = _clean_text(a.get_text()) or slug
            hubs[slug] = DesignazioniHub(slug=slug, base_url=base, label=label)
        return sorted(hubs.values(), key=lambda h: h.label.lower())
    finally:
        if own_client:
            client.close()


def scrape_designazioni_hubs(
    filter_section: Optional[str] = "Legnano",
    max_des_pages_per_hub: Optional[int] = None,
    request_delay: float = 0.35,
    *,
    skip_slugs: Optional[frozenset[str]] = None,
    only_slugs: Optional[frozenset[str]] = None,
) -> ScrapeResult:
    """Crawl ogni hub (gir.asp → des.asp), filtro sezione arbitrale opzionale."""
    combined = ScrapeResult()
    skip = skip_slugs or frozenset()
    only = only_slugs

    with httpx.Client(headers=DEFAULT_HEADERS, timeout=30.0) as client:
        hubs = discover_designazioni_hubs(client)
        for hub in hubs:
            if hub.slug in skip:
                continue
            if only is not None and hub.slug not in only:
                continue
            source = (
                "aia-figc-lombardia"
                if hub.slug == "lombardia"
                else f"aia-figc-{hub.slug}"
            )
            try:
                scraper = AiaLombardiaScraper(
                    section_gare="",
                    base_url=hub.base_url,
                    request_delay=request_delay,
                    source=source,
                )
                part = scraper.scrape(
                    filter_section=filter_section,
                    max_des_pages=max_des_pages_per_hub,
                    source=source,
                )
                combined.items.extend(part.items)
                combined.pages_fetched += part.pages_fetched
                combined.errors.extend([f"[{hub.slug}] {e}" for e in part.errors])
                logger.info(
                    "Hub %s: %d righe (filtro=%s)",
                    hub.slug,
                    len(part.items),
                    filter_section or "—",
                )
            except Exception as e:
                combined.errors.append(f"[{hub.slug}] hub: {e}")

    logger.info(
        "Crawl hub designazioni: %d righe, %d pagine, %d hub, %d errori",
        len(combined.items),
        combined.pages_fetched,
        len(hubs),
        len(combined.errors),
    )
    return combined


def resolve_lombardia_section_gare(
    filter_section: Optional[str],
    client: Optional[httpx.Client] = None,
) -> str:
    """Codice gare sezione (es. 3-270 per Legnano) dalla tabella CRA Lombardia."""
    if not filter_section:
        return ""
    from .aia_lombardia import AiaLombardiaScraper
    from ..designation_legnano import section_matches

    own = client is None
    if own:
        client = httpx.Client(headers=DEFAULT_HEADERS, timeout=30.0)
    try:
        for sec in AiaLombardiaScraper.list_lombardia_sections(client):
            if section_matches(sec.get("label", ""), filter_section):
                return (sec.get("gare") or "").strip()
    finally:
        if own:
            client.close()
    return ""


def scrape_lombardia_all_sections(
    filter_section: Optional[str] = "Legnano",
    max_des_pages: Optional[int] = None,
    request_delay: float = 0.35,
) -> ScrapeResult:
    """Solo Lombardia — sezione CRA (es. Legnano gare=3-270)."""
    with httpx.Client(headers=DEFAULT_HEADERS, timeout=30.0) as client:
        section_gare = resolve_lombardia_section_gare(filter_section, client)
    scraper = AiaLombardiaScraper(
        section_gare=section_gare,
        base_url="https://www.aia-figc.it/designazioni/lombardia/",
        request_delay=request_delay,
        source="aia-figc-lombardia",
    )
    return scraper.scrape(
        filter_section=filter_section,
        max_des_pages=max_des_pages,
        source="aia-figc-lombardia",
    )
