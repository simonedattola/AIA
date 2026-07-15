"""Scrape documenti da https://www.aia-legnano.it/download/"""
from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from ..document_sections import DEFAULT_DOCUMENT_SECTIONS, normalize_section_name
from .aia_downloads import ScrapedDownload, _clean_query, import_scraped_downloads

logger = logging.getLogger(__name__)

DOWNLOAD_PAGE = "https://www.aia-legnano.it/download/"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AIA-Legnano-CMS/1.0; +https://www.aia-legnano.it)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Referer": DOWNLOAD_PAGE,
}

SOURCE = "aia-legnano-download"
SORT_BASE = 1000

FIGC_URL_REPLACEMENTS = {
    "https://www.aia-figc.it/download/regolamenti/reg_2022.pdf": "https://www.aia-figc.it/download/regolamenti/reg_2025.pdf",
    "https://www.aia-figc.it/download/regolamenti/reg_2022_c5.pdf": "https://www.aia-figc.it/download/regolamenti/reg_2025_c5.pdf",
}

_TITLE_SECTION = (
    (re.compile(r"regolamento\s+calcio", re.I), DEFAULT_DOCUMENT_SECTIONS[0]),
    (re.compile(r"^regolamento", re.I), DEFAULT_DOCUMENT_SECTIONS[0]),
    (re.compile(r"circolare", re.I), DEFAULT_DOCUMENT_SECTIONS[3]),
)


def _section_for_title(title: str) -> str:
    for pattern, section in _TITLE_SECTION:
        if pattern.search(title or ""):
            return section
    return DEFAULT_DOCUMENT_SECTIONS[3]


def _normalize_href(href: str, base: str) -> str:
    href = (href or "").strip()
    if href.endswith("/span"):
        href = href[: -len("/span")]
    return _clean_query(urljoin(base, href))


def _title_for_link(link) -> str:
    tr = link.find_parent("tr")
    if tr:
        first_td = tr.find("td")
        if first_td:
            return first_td.get_text(" ", strip=True)
    td = link.find_parent("td")
    if td:
        prev = td.find_previous_sibling("td")
        if prev:
            return prev.get_text(" ", strip=True)
    text = link.get_text(" ", strip=True)
    if text and text.lower() != "link":
        return text
    path = urlparse(link.get("href") or "").path
    return path.rsplit("/", 1)[-1].replace("_", " ").replace("-", " ")


def _is_download_href(href: str, page_url: str) -> bool:
    if not href:
        return False
    low = href.lower()
    if low.rstrip("/") in ("/download", "download", page_url.rstrip("/")):
        return False
    if "aia-legnano.it/download" in low and not any(
        ext in low for ext in (".pdf", ".doc", ".docx", ".zip", ".pptx", ".mp3", "/documents/")
    ):
        return False
    return any(
        ext in low
        for ext in (
            ".pdf",
            ".doc",
            ".docx",
            ".zip",
            ".pptx",
            ".mp3",
            "/documents/",
            "aia-figc.it",
            "drive.google.com",
        )
    )


def scrape_legnano_downloads(client: httpx.Client | None = None) -> list[ScrapedDownload]:
    own = client is None
    if own:
        client = httpx.Client(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=60.0)
    try:
        res = client.get(DOWNLOAD_PAGE)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        wrap = soup.select_one(".page-content-wrap") or soup
        items: list[ScrapedDownload] = []
        seen: set[str] = set()

        for link in wrap.select("a[href]"):
            href = _normalize_href(link.get("href"), DOWNLOAD_PAGE)
            if not _is_download_href(href, DOWNLOAD_PAGE) or href in seen:
                continue
            seen.add(href)
            title = _title_for_link(link).strip()
            if not title:
                continue
            file_url = FIGC_URL_REPLACEMENTS.get(href, href)
            section_name = normalize_section_name(_section_for_title(title))
            items.append(
                ScrapedDownload(
                    title=title,
                    description="",
                    file_url=file_url,
                    category=section_name,
                    section=section_name,
                    source_url=href,
                )
            )
        return items
    finally:
        if own:
            client.close()


async def import_legnano_downloads(
    db,
    *,
    download_files: bool = True,
    replace_existing: bool = True,
) -> dict:
    scraped = scrape_legnano_downloads()
    return await import_scraped_downloads(
        db,
        scraped,
        source=SOURCE,
        sort_base=SORT_BASE,
        download_files=download_files,
        replace_existing=replace_existing,
        file_prefix="legnano",
    )
