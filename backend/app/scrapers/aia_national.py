"""Scraper hub designazioni nazionali C.A.N. (canc, cand, can5, … — esclusa /can Serie A)."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from .aia_lombardia import (
    DEFAULT_HEADERS,
    ScrapedDesignation,
    ScrapeResult,
    AiaLombardiaScraper,
    _clean_text,
    _external_id,
    _normalize_role,
)

logger = logging.getLogger(__name__)

DETTAGLIO_RE = re.compile(r"dettaglio\.asp\?ID=(\d+)", re.I)
TEAM_SEP = r"[–\-]"
MATCH_START_RE = re.compile(
    rf"(?P<home>[A-Z][A-Z0-9\s\.'\u2019]+?)\s*{TEAM_SEP}\s*"
    rf"(?P<away>[A-Z][A-Z0-9\s\.'\u2019]+?)\s+"
    r".*?"
    r"(?P<date>\d{1,2}/\d{1,2})",
    re.I,
)
OFFICIAL_TAIL_RE = re.compile(r"\b(IV|VAR|AVAR|OAR)\s*:\s*", re.I)
TIME_PREFIX_RE = re.compile(r"^\s*(?:h\.?\s*\d{1,2}\.?\d{0,2})?\s*", re.I)


@dataclass(frozen=True)
class NationalHub:
    slug: str
    base_url: str
    mode: str  # dettaglio | gir_des
    source: str
    label: str


# /designazioni/can/ (Serie A, dettaglio.asp) escluso: solo cognomi, poco affidabile per la sezione.
NATIONAL_HUBS: tuple[NationalHub, ...] = (
    NationalHub(
        "canc",
        "https://www.aia-figc.it/designazioni/canc/",
        "gir_des",
        "aia-figc-canc",
        "C.A.N. C",
    ),
    NationalHub(
        "cand",
        "https://www.aia-figc.it/designazioni/cand/",
        "gir_des",
        "aia-figc-cand",
        "C.A.N. D",
    ),
    NationalHub(
        "can5elite",
        "https://www.aia-figc.it/designazioni/can5elite/",
        "gir_des",
        "aia-figc-can5elite",
        "C.A.N. 5 Elite",
    ),
    NationalHub(
        "can5",
        "https://www.aia-figc.it/designazioni/can5/",
        "gir_des",
        "aia-figc-can5",
        "C.A.N. 5",
    ),
    NationalHub(
        "canbs",
        "https://www.aia-figc.it/designazioni/canbs/",
        "gir_des",
        "aia-figc-canbs",
        "C.A.N. BS",
    ),
)


def _dd_mm_to_iso(dd_mm: str, ref: date | None = None) -> str:
    ref = ref or datetime.utcnow().date()
    m = re.match(r"(\d{1,2})/(\d{1,2})", dd_mm or "")
    if not m:
        return "1970-01-01"
    d, mo = int(m.group(1)), int(m.group(2))
    y = ref.year
    if mo >= 7 and ref.month < 7:
        y = ref.year - 1
    elif mo < 7 and ref.month >= 7:
        y = ref.year
    return f"{y}-{mo:02d}-{d:02d}"


def _parse_tail_officials(segment: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    markers = list(OFFICIAL_TAIL_RE.finditer(segment))
    for i, m in enumerate(markers):
        role = m.group(1).upper()
        start = m.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(segment)
        name = _clean_text(segment[start:end])
        if name:
            out.append((role, name))
    return out


def _parse_national_officials(refs: str) -> list[tuple[str, str]]:
    refs = _clean_text(refs)
    if not refs:
        return []
    out: list[tuple[str, str]] = []

    tail_match = OFFICIAL_TAIL_RE.search(refs)
    head = refs[: tail_match.start()].strip() if tail_match else refs
    tail_text = refs[tail_match.start() :] if tail_match else ""

    if head:
        if re.search(TEAM_SEP, head):
            left, right = re.split(TEAM_SEP, head, maxsplit=1)
            left_tokens = _clean_text(left).split()
            right_tokens = _clean_text(right).split()
            if left_tokens:
                out.append(("Arbitro", left_tokens[0]))
            assistants = left_tokens[1:] + right_tokens
            if len(assistants) >= 1:
                out.append(("Assistente 1", assistants[0]))
            if len(assistants) >= 2:
                out.append(("Assistente 2", assistants[1]))
        else:
            out.append(("Arbitro", head))

    out.extend(_parse_tail_officials(tail_text))
    return out


def parse_dettaglio_page(
    html: str, page_url: str, detail_id: str, hub: NationalHub
) -> list[ScrapedDesignation]:
    """Parse dettaglio.asp (testo libero, es. Serie A su /designazioni/can/)."""
    soup = BeautifulSoup(html, "html.parser")
    championship = ""
    h1 = soup.find("h1")
    if h1:
        championship = _clean_text(h1.get_text())

    content = soup.select_one("#content") or soup.select_one(".content-wrap")
    if not content:
        return []
    text = content.get_text(" ", strip=True)
    if "Supplemento on-line" in text:
        text = text.split("Supplemento on-line")[0].strip()

    out: list[ScrapedDesignation] = []
    starts = list(MATCH_START_RE.finditer(text))
    for i, m in enumerate(starts):
        home = _clean_text(m.group("home"))
        away = _clean_text(m.group("away"))
        if not home or not away:
            continue
        match_date = _dd_mm_to_iso(m.group("date") or "")
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        refs_raw = text[m.end() : end]
        refs_raw = TIME_PREFIX_RE.sub("", refs_raw, count=1)
        match_label = f"{home} - {away}"
        gare = f"{hub.slug}-dettaglio-{detail_id}"

        for role_raw, name in _parse_national_officials(refs_raw):
            if role_raw.upper() in ("IV", "VAR", "AVAR", "OAR"):
                role = role_raw.upper()
            else:
                role = _normalize_role(role_raw)
            if not name:
                continue
            out.append(
                ScrapedDesignation(
                    external_id=_external_id(match_date, home, away, role, name),
                    match_date=match_date,
                    championship=championship or hub.label,
                    match_home=home,
                    match_away=away,
                    match_label=match_label,
                    role=role,
                    member_name=name,
                    referee_section="",
                    gare_code=gare,
                    source=hub.source,
                )
            )
    return out


def discover_dettaglio_ids(html: str) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for m in DETTAGLIO_RE.finditer(html):
        did = m.group(1)
        if did not in seen:
            seen.add(did)
            ids.append(did)
    return ids


def scrape_national_hubs(
    filter_section: Optional[str] = "Legnano",
    max_dettaglio_pages: Optional[int] = None,
    max_des_pages_per_hub: Optional[int] = None,
    hubs: tuple[NationalHub, ...] = NATIONAL_HUBS,
    request_delay: float = 0.35,
) -> ScrapeResult:
    """Crawl all configured national hubs."""
    combined = ScrapeResult()

    with httpx.Client(headers=DEFAULT_HEADERS, timeout=30.0) as client:
        for hub in hubs:
            try:
                if hub.mode == "gir_des":
                    scraper = AiaLombardiaScraper(
                        section_gare="",
                        base_url=hub.base_url,
                        request_delay=request_delay,
                        source=hub.source,
                    )
                    part = scraper.scrape(
                        filter_section=filter_section,
                        max_des_pages=max_des_pages_per_hub,
                        source=hub.source,
                    )
                    combined.items.extend(part.items)
                    combined.pages_fetched += part.pages_fetched
                    combined.errors.extend([f"[{hub.slug}] {e}" for e in part.errors])
                    continue

                base = hub.base_url
                time.sleep(request_delay)
                html = client.get(base, follow_redirects=True).text
                combined.pages_fetched += 1
                detail_ids = discover_dettaglio_ids(html)
                if max_dettaglio_pages:
                    detail_ids = detail_ids[:max_dettaglio_pages]

                for did in detail_ids:
                    try:
                        time.sleep(request_delay)
                        url = urljoin(
                            "https://www.aia-figc.it/", f"dettaglio.asp?ID={did}"
                        )
                        dhtml = client.get(url, follow_redirects=True).text
                        combined.pages_fetched += 1
                        rows = parse_dettaglio_page(dhtml, url, did, hub)
                        combined.items.extend(rows)
                    except Exception as e:
                        combined.errors.append(f"[{hub.slug}] dettaglio {did}: {e}")
            except Exception as e:
                combined.errors.append(f"[{hub.slug}] hub: {e}")

    logger.info(
        "National scrape: %d designations, %d pages, %d errors",
        len(combined.items),
        combined.pages_fetched,
        len(combined.errors),
    )
    return combined
