"""Import articoli dal sito WordPress legacy (aia-legnano.it)."""

from __future__ import annotations

import hashlib
import html as html_lib
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import bleach
import httpx
from bs4 import BeautifulSoup
from slugify import slugify

from .article_categories import (
    ensure_category_exists,
    save_configured_categories,
    get_configured_categories,
    merge_categories,
)
from .article_cleanup import is_weekly_designations_article, repair_body_html
from .article_member_match import match_members_by_full_name
from .models import Article, _now
from . import storage as upload_storage

logger = logging.getLogger(__name__)

WP_API = "https://www.aia-legnano.it/wp-json/wp/v2"
WP_SITE = "https://www.aia-legnano.it"
USER_AGENT = "AIA-Legnano-Importer/1.0"

LEGACY_IFRAME_TAGS = ["iframe"]
from .sanitize import ALLOWED_ATTRS as BASE_ATTRS, ALLOWED_TAGS as BASE_TAGS

LEGACY_ALLOWED_TAGS = list(BASE_TAGS) + ["h1", "h5", "h6", "iframe", "time"]
LEGACY_ALLOWED_ATTRS = {
    **BASE_ATTRS,
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height", "loading", "class"],
    "iframe": [
        "src",
        "width",
        "height",
        "frameborder",
        "allow",
        "allowfullscreen",
        "style",
        "scrolling",
    ],
    "p": ["style", "class"],
    "span": ["style", "class"],
    "div": ["class", "role", "id", "style"],
    "time": ["datetime", "class"],
}


def _strip_text(html: str) -> str:
    if not html:
        return ""
    return re.sub(
        r"\s+", " ", BeautifulSoup(html, "lxml").get_text(" ", strip=True)
    ).strip()


def _clean_legacy_html(raw: str) -> str:
    if not raw:
        return ""
    soup = BeautifulSoup(raw, "lxml")
    for tag in soup.select("div.wpcf7, form.wpcf7-form, script"):
        tag.decompose()
    for tag in soup.select("a.moretag"):
        tag.decompose()
    body = soup.body or soup
    inner = "".join(str(c) for c in body.children) if body else str(soup)
    return bleach.clean(
        inner,
        tags=LEGACY_ALLOWED_TAGS,
        attributes=LEGACY_ALLOWED_ATTRS,
        protocols=["http", "https", "mailto"],
        strip=False,
    )


def _format_tag(name: str) -> str:
    n = (name or "").strip()
    if not n:
        return ""
    if n.startswith("#"):
        return n
    if n.islower() and " " not in n:
        return n.replace("-", " ").title()
    return n[0].upper() + n[1:] if n else n


def _infer_category(
    title: str, wp_category_names: list[str], tag_names: list[str]
) -> str:
    t = title.lower()
    tags_l = " ".join(tag_names).lower()
    cats_l = " ".join(wp_category_names).lower()

    if any(
        k in t
        for k in (
            "corso arbitri",
            "corso per arbitri",
            "iscrizioni al corso",
            "nuovo corso",
        )
    ):
        return "Corso arbitri"
    if any(
        k in tags_l
        for k in ("corsoarbitri", "corso arbitri", "nuoviarbitri", "reclutamento")
    ):
        return "Corso arbitri"
    if any(
        k in t
        for k in (
            "promoz",
            "promoss",
            "serie a",
            "serie b",
            "eccellenza",
            "can ",
            "c.a.n",
        )
    ):
        return "Successi"
    if any(k in tags_l for k in ("cra", "premiazione", "talent")):
        return "Successi"
    if any(
        k in t
        for k in (
            "regolamento",
            "riunione tecnica",
            "dogso",
            "ifab",
            "protesta disciplinare",
        )
    ):
        return "Regolamento"
    if "regolamento" in tags_l:
        return "Regolamento"
    if any(
        k in t for k in ("cordoglio", "scomparsa", "ciao,", "commemor", "benemerito")
    ):
        return "Vita sezionale"
    if any(k in t for k in ("raduno", "raduni")):
        return "Raduni"
    if any(k in t for k in ("festa", "grigliata", "cena", "assemblea")):
        return "Vita sezionale"
    if "designazioni" in tags_l and "designazioni" in t:
        return "Comunicazioni"
    if "notizie" in cats_l:
        return "Comunicazioni"
    return "Vita sezionale"


class LegacyArticleImporter:
    def __init__(self, db, *, download_images: bool = True, dry_run: bool = False):
        self.db = db
        self.download_images = download_images
        self.dry_run = dry_run
        self._image_cache: dict[str, str] = {}
        self._members: list[dict] = []
        self._wp_categories: dict[int, str] = {}
        self._wp_tags: dict[int, str] = {}

    async def _load_taxonomies(self, client: httpx.AsyncClient) -> None:
        for page in range(1, 20):
            r = await client.get(
                f"{WP_API}/categories", params={"per_page": 100, "page": page}
            )
            if r.status_code != 200 or not r.json():
                break
            for c in r.json():
                self._wp_categories[c["id"]] = c.get("name") or c.get("slug", "")
        for page in range(1, 20):
            r = await client.get(
                f"{WP_API}/tags", params={"per_page": 100, "page": page}
            )
            if r.status_code != 200 or not r.json():
                break
            for t in r.json():
                self._wp_tags[t["id"]] = t.get("name") or t.get("slug", "")

    async def _load_members(self) -> None:
        self._members = await self.db.members.find(
            {}, {"_id": 0, "id": 1, "firstName": 1, "lastName": 1, "slug": 1}
        ).to_list(500)

    def _ext_from_url(self, url: str) -> str:
        path = urlparse(url).path
        ext = Path(path).suffix.lower()
        if ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            return ext
        return ".jpg"

    async def _mirror_url(
        self, client: httpx.AsyncClient, url: str, wp_post_id: int
    ) -> str:
        url = (url or "").strip()
        if not url:
            return ""
        if url in self._image_cache:
            return self._image_cache[url]
        if not url.startswith(WP_SITE) and not url.startswith("http"):
            return url
        if not self.download_images or self.dry_run:
            self._image_cache[url] = url
            return url
        if not url.startswith(WP_SITE):
            self._image_cache[url] = url
            return url

        try:
            resp = await client.get(url, timeout=60.0)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("Download immagine fallito %s: %s", url, exc)
            self._image_cache[url] = url
            return url

        ext = self._ext_from_url(url)
        digest = hashlib.md5(url.encode()).hexdigest()[:10]
        name = f"legacy-wp{wp_post_id}-{digest}{ext}"
        upload_storage.save_bytes(name, resp.content)
        local = f"/api/uploads/{name}"
        self._image_cache[url] = local
        return local

    async def _mirror_html_images(
        self, client: httpx.AsyncClient, html: str, wp_post_id: int
    ) -> str:
        if not html:
            return ""
        soup = BeautifulSoup(html, "lxml")
        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                img["src"] = await self._mirror_url(client, src, wp_post_id)
            img.attrs.pop("srcset", None)
            img.attrs.pop("sizes", None)
        body = soup.body
        if body:
            return "".join(str(c) for c in body.children)
        return str(soup)

    def _extract_terms(self, post: dict) -> tuple[list[str], list[str]]:
        cat_names: list[str] = []
        tag_names: list[str] = []
        embedded = post.get("_embedded") or {}
        for group in embedded.get("wp:term") or []:
            for term in group or []:
                if term.get("taxonomy") == "category":
                    cat_names.append(term.get("name") or "")
                elif term.get("taxonomy") == "post_tag":
                    tag_names.append(_format_tag(term.get("name") or ""))
        for cid in post.get("categories") or []:
            if cid in self._wp_categories:
                cat_names.append(self._wp_categories[cid])
        for tid in post.get("tags") or []:
            if tid in self._wp_tags:
                tag_names.append(_format_tag(self._wp_tags[tid]))
        return cat_names, list(dict.fromkeys(t for t in tag_names if t))

    def _featured_url(self, post: dict) -> str:
        embedded = post.get("_embedded") or {}
        media = embedded.get("wp:featuredmedia") or []
        if not media:
            return ""
        item = media[0]
        return item.get("source_url") or item.get("guid", {}).get("rendered") or ""

    async def fetch_all_posts(self, client: httpx.AsyncClient) -> list[dict]:
        posts: list[dict] = []
        page = 1
        while True:
            r = await client.get(
                f"{WP_API}/posts",
                params={
                    "per_page": 100,
                    "page": page,
                    "status": "publish",
                    "_embed": "wp:featuredmedia,wp:term",
                },
            )
            if r.status_code == 404:
                break
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            posts.extend(batch)
            total_pages = int(r.headers.get("X-WP-TotalPages", "1"))
            if page >= total_pages:
                break
            page += 1
        return posts

    async def import_post(
        self, client: httpx.AsyncClient, post: dict
    ) -> dict[str, Any]:
        wp_id = int(post["id"])
        title = html_lib.unescape(post.get("title", {}).get("rendered") or "").strip()
        slug = (post.get("slug") or slugify(title)).strip()
        date_raw = post.get("date_gmt") or post.get("date") or ""
        published_at = date_raw
        if published_at and not published_at.endswith("Z") and "+" not in published_at:
            published_at = (
                f"{published_at}+00:00"
                if "T" in published_at
                else f"{published_at}T12:00:00+00:00"
            )

        cat_names, _tag_names = self._extract_terms(post)
        category = _infer_category(title, cat_names, [])

        raw_html = post.get("content", {}).get("rendered") or ""
        body_html = repair_body_html(_clean_legacy_html(raw_html))
        if is_weekly_designations_article(
            {"title": title, "slug": slug, "bodyHtml": body_html}
        ):
            return {
                "action": "skipped",
                "slug": slug,
                "title": title,
                "reason": "designazioni",
            }
        if self.download_images and not self.dry_run:
            body_html = await self._mirror_html_images(client, body_html, wp_id)

        cover_remote = self._featured_url(post)
        if not cover_remote:
            soup = BeautifulSoup(body_html, "lxml")
            first_img = soup.find("img")
            if first_img and first_img.get("src"):
                cover_remote = first_img["src"]
        cover_url = ""
        if cover_remote:
            if cover_remote.startswith("/api/"):
                cover_url = cover_remote
            else:
                cover_url = await self._mirror_url(client, cover_remote, wp_id)

        excerpt_html = post.get("excerpt", {}).get("rendered") or ""
        excerpt = _strip_text(excerpt_html) or _strip_text(body_html)[:280]

        related_ids = match_members_by_full_name(
            title, body_html, self._members, excerpt=excerpt
        )

        existing = await self.db.articles.find_one(
            {"$or": [{"legacyWpId": wp_id}, {"slug": slug}]},
            {"_id": 0, "id": 1, "slug": 1, "legacyWpId": 1},
        )
        if existing and existing.get("legacyWpId") != wp_id:
            slug = f"{slug}-wp{wp_id}"

        doc = Article(
            slug=slug,
            title=title,
            category=category,
            excerpt=excerpt,
            bodyHtml=body_html,
            coverUrl=cover_url,
            relatedMemberIds=related_ids,
            tags=[],
            legacyWpId=wp_id,
            status="published",
            publishedAt=published_at,
        )
        payload = doc.model_dump()
        payload["updatedAt"] = _now()

        if self.dry_run:
            return {
                "action": "dry-run",
                "slug": slug,
                "title": title,
                "category": category,
            }

        if existing:
            payload["id"] = existing["id"]
            payload["createdAt"] = existing.get("createdAt") or _now()
            await self.db.articles.update_one({"id": existing["id"]}, {"$set": payload})
            return {"action": "updated", "slug": slug, "title": title}

        await self.db.articles.insert_one(payload.copy())
        return {"action": "created", "slug": slug, "title": title}

    async def run(self) -> dict[str, Any]:
        upload_storage.ensure_local_dir()
        await self._load_members()

        stats = {
            "created": 0,
            "updated": 0,
            "errors": 0,
            "categories": set(),
            "dry_run": self.dry_run,
        }
        imported_categories: list[str] = []

        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=90.0,
        ) as client:
            await self._load_taxonomies(client)
            posts = await self.fetch_all_posts(client)
            stats["total_wp"] = len(posts)

            for post in posts:
                try:
                    result = await self.import_post(client, post)
                    stats["categories"].add(result.get("category", ""))
                    imported_categories.append(result.get("category", ""))
                    if result.get("action") == "created":
                        stats["created"] += 1
                    elif result.get("action") == "updated":
                        stats["updated"] += 1
                except Exception as exc:
                    logger.exception("Import post %s failed: %s", post.get("id"), exc)
                    stats["errors"] += 1

        if not self.dry_run:
            configured = await get_configured_categories(self.db)
            await save_configured_categories(
                self.db, merge_categories(configured, imported_categories)
            )
            for cat in imported_categories:
                if cat:
                    await ensure_category_exists(self.db, cat)

        stats["categories"] = sorted(c for c in stats["categories"] if c)
        return stats


async def run_legacy_article_import(
    db, *, dry_run: bool = False, download_images: bool = True
) -> dict[str, Any]:
    importer = LegacyArticleImporter(
        db, dry_run=dry_run, download_images=download_images
    )
    return await importer.run()
