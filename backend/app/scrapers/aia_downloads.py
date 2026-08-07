"""Scrape documenti da https://www.aia-figc.it/download/"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from ..media_urls import format_file_size_label
from ..paths import UPLOAD_DIR

logger = logging.getLogger(__name__)

DOWNLOAD_PAGE = "https://www.aia-figc.it/download/"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AIA-Legnano-CMS/1.0; +https://www.aia-legnano.it)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Referer": DOWNLOAD_PAGE,
}

FILE_HEADERS = {
    **DEFAULT_HEADERS,
    "Accept": "application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/octet-stream,*/*;q=0.8",
}

FIGC_SOURCE = "aia-figc-download"
FIGC_SORT_BASE = 10


@dataclass
class ScrapedDownload:
    title: str
    description: str
    file_url: str
    category: str
    section: str
    source_url: str


def _clean_query(url: str) -> str:
    parsed = urlparse(url)
    return parsed._replace(query="", fragment="").geturl()


def scrape_aia_downloads(client: httpx.Client | None = None) -> list[ScrapedDownload]:
    own = client is None
    if own:
        client = httpx.Client(
            headers=DEFAULT_HEADERS, follow_redirects=True, timeout=60.0
        )
    try:
        res = client.get(DOWNLOAD_PAGE)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        items: list[ScrapedDownload] = []
        current_section = ""

        for el in soup.select("h2, .feature-box"):
            if el.name == "h2":
                current_section = el.get_text(" ", strip=True)
                continue
            link = el.select_one("a[href]")
            if not link:
                continue
            href = (link.get("href") or "").strip()
            if not href or href.rstrip("/") in ("/download", "download"):
                continue
            title_el = el.select_one("h3")
            title = (
                title_el.get_text(" ", strip=True)
                if title_el
                else link.get_text(" ", strip=True)
            )
            if not title:
                continue
            desc_el = el.select_one("p")
            description = desc_el.get_text(" ", strip=True) if desc_el else ""
            file_url = _clean_query(urljoin(DOWNLOAD_PAGE, href))
            section_name = current_section.strip()
            items.append(
                ScrapedDownload(
                    title=title,
                    description=description,
                    file_url=file_url,
                    category=section_name,
                    section=section_name,
                    source_url=file_url,
                )
            )
        return items
    finally:
        if own:
            client.close()


def _local_name_from_url(url: str) -> str:
    name = urlparse(url).path.rsplit("/", 1)[-1] or "documento.bin"
    return re.sub(r"[^\w.\-]+", "_", name)


def _can_download_file(url: str) -> bool:
    host = (urlparse(url).netloc or "").lower()
    if "drive.google.com" in host:
        return False
    return True


async def import_scraped_downloads(
    db,
    scraped: list[ScrapedDownload],
    *,
    source: str,
    sort_base: int,
    download_files: bool = True,
    replace_existing: bool = True,
    file_prefix: str = "aia",
) -> dict:
    if not scraped:
        return {"scraped": 0, "imported": 0, "skipped": 0, "errors": 0}

    if replace_existing:
        await db.documents.delete_many({"source": source})
        if source == FIGC_SOURCE:
            await db.documents.delete_many(
                {"fileUrl": {"$in": ["#", "https://www.figc.it/"]}}
            )

    imported = skipped = errors = 0

    async with httpx.AsyncClient(
        headers=FILE_HEADERS, follow_redirects=True, timeout=120.0
    ) as client:
        for i, item in enumerate(scraped):
            stored_url = item.file_url
            file_size = ""

            if download_files and _can_download_file(item.file_url):
                try:
                    referer = f"{urlparse(item.file_url).scheme}://{urlparse(item.file_url).netloc}/"
                    res = await client.get(
                        item.file_url,
                        headers={**FILE_HEADERS, "Referer": referer},
                    )
                    res.raise_for_status()
                    suffix = (
                        Path(_local_name_from_url(item.file_url)).suffix.lower()
                        or ".bin"
                    )
                    name = f"{file_prefix}_{uuid.uuid4().hex[:12]}{suffix}"
                    target = UPLOAD_DIR / name
                    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(res.content)
                    file_size = format_file_size_label(len(res.content))
                    stored_url = f"/api/uploads/{name}"
                except Exception as exc:
                    logger.warning("Download fallito %s: %s", item.file_url, exc)
                    errors += 1

            existing = await db.documents.find_one(
                {"source": source, "sourceUrl": item.source_url},
                {"_id": 0, "id": 1},
            )
            if existing and not replace_existing:
                skipped += 1
                continue

            section_name = (item.section or item.category or "").strip()
            doc = {
                "id": existing["id"] if existing else uuid.uuid4().hex,
                "title": item.title.strip(),
                "description": item.description,
                "fileUrl": stored_url,
                "fileSize": file_size,
                "category": section_name,
                "sortOrder": sort_base + i,
                "source": source,
                "sourceUrl": item.source_url,
                "section": section_name,
            }
            if existing:
                await db.documents.update_one({"id": doc["id"]}, {"$set": doc})
            else:
                await db.documents.insert_one(doc.copy())
            imported += 1

    logger.info(
        "Import documenti %s: %s trovati, %s importati, %s errori",
        source,
        len(scraped),
        imported,
        errors,
    )
    return {
        "scraped": len(scraped),
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    }


async def import_aia_downloads(
    db,
    *,
    download_files: bool = True,
    replace_existing: bool = True,
) -> dict:
    scraped = scrape_aia_downloads()
    return await import_scraped_downloads(
        db,
        scraped,
        source=FIGC_SOURCE,
        sort_base=FIGC_SORT_BASE,
        download_files=download_files,
        replace_existing=replace_existing,
        file_prefix="aia",
    )
