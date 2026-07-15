"""Scraper for AIA FIGC Lombardia designazioni (ASP classic site).

Hierarchy:
  default.asp?gare=3-270  -> category links (gir.asp)
  gir.asp?gare=3-270-SEC  -> matchday links (des.asp)
  des.asp?gare=3-270-SEC-R -> match table with referees
"""
from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Iterable, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.aia-figc.it/designazioni/lombardia/"
DEFAULT_HEADERS = {
    "User-Agent": "AIA-Legnano-Platform/1.0 (+https://aia-legnano.it; designazioni-sync)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "it-IT,it;q=0.9",
}

DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
GARE_RE = re.compile(r"gare=([^&\"']+)", re.I)

ROLE_MAP = {
    "arbitro": "Arbitro",
    "assistente 1": "Assistente 1",
    "assistente 2": "Assistente 2",
    "assistente": "Assistente",
    "osservatore": "Osservatore",
    "osservatore 1": "Osservatore",
    "osservatore 2": "Osservatore",
    "quarto uomo": "Arbitro",
}


@dataclass
class ScrapedDesignation:
    external_id: str
    match_date: str  # ISO date YYYY-MM-DD
    championship: str  # campionato (es. SECONDA CATEGORIA)
    match_home: str
    match_away: str
    match_label: str
    role: str
    member_name: str
    referee_section: str = ""
    gare_code: str = ""
    match_day: str = ""  # giornata
    girone: str = ""
    source: str = "aia-figc-lombardia"


@dataclass
class ScrapeResult:
    items: list[ScrapedDesignation] = field(default_factory=list)
    pages_fetched: int = 0
    errors: list[str] = field(default_factory=list)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\ufeff", "")).strip()


def _normalize_role(header: str) -> str:
    key = _clean_text(header).lower()
    return ROLE_MAP.get(key, _clean_text(header) or "Arbitro")


def _parse_referee_cell(td) -> tuple[str, str]:
    """Return (name, section) from a referee table cell."""
    if td is None:
        return "", ""
    section_div = td.find("div", class_="designazione-sezione")
    section = _clean_text(section_div.get_text()) if section_div else ""
    if section_div:
        section_div.decompose()
    name = _clean_text(td.get_text())
    return name, section


def _parse_match_date_from_h3(h3_text: str) -> tuple[str, str, str]:
    """Extract ISO date, girone label, giornata from h3."""
    text = _clean_text(h3_text)
    girone = ""
    giornata = ""
    iso = ""

    m_date = DATE_RE.search(text)
    if m_date:
        d, mo, y = m_date.groups()
        iso = f"{y}-{int(mo):02d}-{int(d):02d}"

    m_g = re.search(r"girone\s+([^\-]+)", text, re.I)
    if m_g:
        girone = _clean_text(m_g.group(1))
    m_day = re.search(r"giornata\s+(\d+)", text, re.I)
    if m_day:
        giornata = m_day.group(1)

    return iso, girone, giornata


def _external_id(match_date: str, home: str, away: str, role: str, name: str) -> str:
    """Chiave stabile per la stessa designazione su hub/gare diversi."""
    raw = f"{match_date}|{home}|{away}|{role}|{name}".lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def parse_des_page(html: str, page_url: str, gare: str) -> list[ScrapedDesignation]:
    """Parse a des.asp page into designation rows."""
    soup = BeautifulSoup(html, "html.parser")
    championship = ""
    h2 = soup.find("h2")
    if h2:
        championship = _clean_text(h2.get_text())

    match_date = ""
    girone = ""
    giornata = ""
    h3 = soup.find("h3")
    if h3:
        match_date, girone, giornata = _parse_match_date_from_h3(h3.get_text())

    if not match_date:
        logger.warning("No date on %s", page_url)

    out: list[ScrapedDesignation] = []
    for table in soup.select("table.table"):
        header_row = table.select_one("tr.table-header-designazioni")
        if not header_row:
            continue
        ths = header_row.find_all("th")
        if not ths or "gara" not in _clean_text(ths[0].get_text()).lower():
            continue

        # Header "Gara" uses colspan=2 but only one <th>; role columns must use
        # cumulative TD index (0=home, 1=away, 2=arbitro, …).
        role_headers: list[tuple[int, str]] = []
        td_col = 0
        for th in ths:
            label = _clean_text(th.get_text())
            hl = label.lower()
            colspan = int(th.get("colspan") or 1)
            if "gara" in hl:
                td_col += colspan
                continue
            if any(k in hl for k in ("arbitro", "assistente", "osservatore", "quarto")):
                role_headers.append((td_col, _normalize_role(label)))
                td_col += colspan
            else:
                td_col += colspan

        for tr in table.find_all("tr"):
            if "table-header-designazioni" in (tr.get("class") or []):
                continue
            tds = tr.find_all("td")
            if len(tds) < 3:
                continue
            home = _clean_text(tds[0].get_text())
            away = _clean_text(tds[1].get_text())
            if not home or not away:
                continue
            match_label = f"{home} - {away}"

            for col_idx, role in role_headers:
                if col_idx >= len(tds):
                    continue
                name, section = _parse_referee_cell(tds[col_idx])
                if not name:
                    continue
                out.append(
                    ScrapedDesignation(
                        external_id=_external_id(match_date or "1970-01-01", home, away, role, name),
                        match_date=match_date or "1970-01-01",
                        championship=championship,
                        match_home=home,
                        match_away=away,
                        match_label=match_label,
                        role=role,
                        member_name=name,
                        referee_section=section,
                        gare_code=gare,
                        match_day=giornata,
                        girone=girone,
                    )
                )
    return out


def _extract_links(html: str, base_url: str, pattern: str) -> list[str]:
    """Return absolute URLs matching asp file pattern (gir.asp or des.asp)."""
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if pattern not in href.lower():
            continue
        if "gare=" not in href.lower():
            continue
        full = urljoin(base_url, href)
        if full not in seen:
            seen.add(full)
            links.append(full)
    return links


def _gare_from_url(url: str) -> str:
    m = GARE_RE.search(url)
    return m.group(1) if m else ""


def _gare_suffix_after_prefix(gare_code: str, prefix: str) -> str:
    """Es. gare=3-270-SEC-R, prefix=3-270 → SEC-R."""
    code = (gare_code or "").strip()
    pre = (prefix or "").strip()
    if not code or not pre or not code.startswith(pre + "-"):
        return ""
    return code[len(pre) + 1 :]


def _regional_gir_suffixes(gir_urls: list[str]) -> list[str]:
    """Suffissi campionato dal CRA Lombardia (gare=3-0-SEC → SEC)."""
    suffixes: list[str] = []
    seen: set[str] = set()
    for url in gir_urls:
        gare = _gare_from_url(url)
        if not gare:
            continue
        parts = gare.split("-")
        if len(parts) < 3:
            continue
        # 3-0-SEC, 3-0-C5J, …
        if parts[0] == "3" and parts[1] == "0":
            suf = "-".join(parts[2:])
        else:
            suf = _gare_suffix_after_prefix(gare, f"{parts[0]}-{parts[1]}")
        if suf and suf not in seen:
            seen.add(suf)
            suffixes.append(suf)
    return suffixes


def discover_gir_urls_for_section(
    client: httpx.Client,
    base_url: str,
    section_gare: str,
    fetch_html,
) -> list[str]:
    """
    Il sito AIA non elenca più gir.asp nella pagina sezione (Default.asp?gare=3-270).
    Si derivano i gironi dal CRA Lombardia (3-0-*) applicando il prefisso sezione (3-270-*).
    """
    base = base_url.rstrip("/") + "/"
    regional_html = fetch_html(client, base)
    regional_girs = _extract_links(regional_html, base, "gir.asp")
    suffixes = _regional_gir_suffixes(regional_girs)
    found: list[str] = []
    seen: set[str] = set()
    for suf in suffixes:
        gir_url = f"{base}gir.asp?gare={section_gare}-{suf}"
        if gir_url in seen:
            continue
        seen.add(gir_url)
        try:
            html = fetch_html(client, gir_url)
            if _extract_links(html, base, "des.asp"):
                found.append(gir_url)
        except Exception as e:
            logger.debug("gir skip %s: %s", gir_url, e)
    logger.info(
        "Gironi sezione %s: %d/%d con designazioni",
        section_gare,
        len(found),
        len(suffixes),
    )
    return found


def _discover_section_index_urls(html: str, base_url: str) -> list[str]:
    """Link default.asp?gare=… (sotto-sezioni regionali su hub CRA)."""
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "default.asp" not in href.lower() or "gare=" not in href.lower():
            continue
        full = urljoin(base_url, href)
        if full not in seen:
            seen.add(full)
            urls.append(full)
    return urls


class AiaLombardiaScraper:
    """Crawl AIA FIGC designazioni hub (Lombardia sezione o hub C.A.N. nazionali)."""

    def __init__(
        self,
        section_gare: str = "3-270",
        base_url: str = BASE_URL,
        request_delay: float = 0.35,
        timeout: float = 30.0,
        source: str = "aia-figc-lombardia",
    ):
        self.section_gare = (section_gare or "").strip()
        self.base_url = base_url.rstrip("/") + "/"
        self.request_delay = request_delay
        self.timeout = timeout
        self.source = source
        self.section_index_url = (
            f"{self.base_url}default.asp?gare={self.section_gare}" if self.section_gare else self.base_url
        )

    def fetch(self, client: httpx.Client, url: str) -> str:
        time.sleep(self.request_delay)
        r = client.get(url, follow_redirects=True)
        r.raise_for_status()
        r.encoding = r.encoding or "utf-8"
        return r.text

    def discover_gir_urls(self, client: httpx.Client) -> list[str]:
        if self.section_gare:
            html = self.fetch(client, self.section_index_url)
            links = _extract_links(html, self.base_url, "gir.asp")
            if links:
                return links
            derived = discover_gir_urls_for_section(
                client,
                self.base_url,
                self.section_gare,
                self.fetch,
            )
            if derived:
                return derived

        html = self.fetch(client, self.base_url)
        links = _extract_links(html, self.base_url, "gir.asp")
        if links:
            return links

        # Lombardia (e altri CRA): i gir.asp sono nelle pagine default.asp di ogni sezione.
        section_urls = _discover_section_index_urls(html, self.base_url)
        if not section_urls and "lombardia" in self.base_url.lower():
            section_urls = [
                s["url"] for s in self.list_lombardia_sections(client)
            ]

        all_gir: list[str] = []
        seen: set[str] = set()
        for sec_url in section_urls:
            try:
                sec_html = self.fetch(client, sec_url)
                for u in _extract_links(sec_html, self.base_url, "gir.asp"):
                    if u not in seen:
                        seen.add(u)
                        all_gir.append(u)
            except Exception as e:
                logger.warning("gir discovery %s: %s", sec_url, e)
        if all_gir:
            return all_gir

        return _extract_links(html, self.base_url, "gir.asp")

    def discover_des_urls(self, client: httpx.Client, gir_url: str) -> list[str]:
        html = self.fetch(client, gir_url)
        return _extract_links(html, self.base_url, "des.asp")

    def scrape(
        self,
        filter_section: Optional[str] = "Legnano",
        max_des_pages: Optional[int] = None,
        source: Optional[str] = None,
    ) -> ScrapeResult:
        """
        Full crawl for the configured section.
        filter_section: if set, only keep rows where referee section matches (case-insensitive).
        """
        result = ScrapeResult()
        row_source = source or self.source
        section_filter = _clean_text(filter_section).lower() if filter_section else ""

        with httpx.Client(headers=DEFAULT_HEADERS, timeout=self.timeout) as client:
            try:
                gir_urls = self.discover_gir_urls(client)
                result.pages_fetched += 1
            except Exception as e:
                result.errors.append(f"section index: {e}")
                return result

            des_urls: list[str] = []
            for gir_url in gir_urls:
                try:
                    des_urls.extend(self.discover_des_urls(client, gir_url))
                    result.pages_fetched += 1
                except Exception as e:
                    result.errors.append(f"gir {gir_url}: {e}")

            # dedupe des urls
            des_urls = list(dict.fromkeys(des_urls))
            if max_des_pages:
                des_urls = des_urls[:max_des_pages]

            for des_url in des_urls:
                try:
                    html = self.fetch(client, des_url)
                    result.pages_fetched += 1
                    gare = _gare_from_url(des_url)
                    rows = parse_des_page(html, des_url, gare)
                    for row in rows:
                        row.source = row_source
                        if section_filter:
                            sec = _clean_text(row.referee_section).lower()
                            if section_filter not in sec:
                                continue
                        result.items.append(row)
                except Exception as e:
                    result.errors.append(f"des {des_url}: {e}")

        logger.info(
            "Scrape gare=%s: %d designations, %d pages, %d errors",
            self.section_gare,
            len(result.items),
            result.pages_fetched,
            len(result.errors),
        )
        return result

    @staticmethod
    def list_lombardia_sections(client: httpx.Client) -> list[dict]:
        """Parse Lombardia hub for section links (Sezioni table)."""
        url = BASE_URL
        r = client.get(url, headers=DEFAULT_HEADERS, timeout=30.0)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        sections = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "default.asp" not in href.lower() or "gare=3-" not in href.lower():
                continue
            label = _clean_text(a.get_text())
            gare = _gare_from_url(urljoin(BASE_URL, href))
            if not gare or not label:
                continue
            sections.append({"label": label, "gare": gare, "url": urljoin(BASE_URL, href)})
        # dedupe by gare
        by_gare: dict[str, dict] = {}
        for s in sections:
            by_gare[s["gare"]] = s
        return sorted(by_gare.values(), key=lambda x: x["label"])
