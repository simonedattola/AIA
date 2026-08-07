"""Galleria pubblica: immagini approvate, upload associati in attesa."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup

from .models import GalleryImage, _id, _now

logger = logging.getLogger(__name__)

ARTICLE_GALLERY_SOURCES = ("article", "article_cover", "article_body")


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _gallery_item_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _article_photo_date(article: dict[str, Any]) -> str:
    pub = (article.get("publishedAt") or "").strip()
    return pub[:10] if len(pub) >= 10 else pub


def _normalize_aspect(aspect: str | None) -> str:
    return aspect if aspect in ("16:9", "9:16") else "16:9"


def _today_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _normalize_gallery_url(url: str) -> str:
    """Chiave per deduplica: URL assoluto senza query/fragment."""
    from .media_urls import resolve_media_url

    u = resolve_media_url((url or "").strip())
    if not u:
        return ""
    if u.startswith("http://") or u.startswith("https://"):
        p = urlparse(u)
        return urlunparse((p.scheme, p.netloc, p.path, "", "", "")).lower()
    return u.lower().rstrip("/")


def _gallery_dedupe_key(item: dict) -> str:
    url = item.get("url") or ""
    norm = _normalize_gallery_url(url)
    if norm:
        return norm
    ch = (item.get("contentHash") or "").strip()
    if ch:
        return f"hash:{ch}"
    return item.get("id", "")


async def dedupe_gallery_images(db) -> int:
    """Rimuove immagini duplicate (stesso URL o hash contenuto)."""
    items = await db.gallery_images.find({}, {"_id": 0}).to_list(5000)
    groups: dict[str, list[dict]] = {}
    for item in items:
        key = _gallery_dedupe_key(item)
        groups.setdefault(key, []).append(item)

    removed = 0
    for group in groups.values():
        if len(group) <= 1:
            continue
        group.sort(
            key=lambda i: (
                1 if i.get("cropEdited") else 0,
                1 if i.get("articleId") else 0,
                -(i.get("sortOrder") or 0),
                i.get("createdAt") or "",
            ),
            reverse=True,
        )
        for dup in group[1:]:
            await db.gallery_images.delete_one({"id": dup["id"]})
            removed += 1
    return removed


def extract_body_images(body_html: str) -> list[dict[str, str]]:
    """Estrae URL univoci delle immagini presenti nel corpo HTML dell'articolo."""
    if not body_html:
        return []
    soup = BeautifulSoup(body_html, "lxml")
    images: list[dict[str, str]] = []
    seen: set[str] = set()
    for img in soup.find_all("img"):
        src = (img.get("src") or "").strip()
        if not src or src in seen:
            continue
        seen.add(src)
        images.append({"url": src, "alt": (img.get("alt") or "").strip()})
    return images


def collect_article_gallery_candidates(article: dict[str, Any]) -> list[dict[str, Any]]:
    """Tutte le immagini candidate da un articolo (copertina + corpo)."""
    from .article_body import normalize_article_body_html

    article_id = (article.get("id") or "").strip()
    if not article_id or article.get("portalOnly"):
        return []

    title = (article.get("title") or "").strip()
    category = (article.get("category") or "").strip()
    photo_date = _article_photo_date(article)
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    cover = (article.get("coverUrl") or "").strip()
    if cover:
        seen.add(cover)
        candidates.append(
            {
                "url": cover,
                "caption": title,
                "category": category,
                "photoDate": photo_date,
                "articleId": article_id,
                "source": "article_cover",
            }
        )

    body = normalize_article_body_html(article.get("bodyHtml") or "")
    for img in extract_body_images(body):
        url = img["url"]
        if url in seen:
            continue
        seen.add(url)
        candidates.append(
            {
                "url": url,
                "caption": (img.get("alt") or "").strip() or title,
                "category": category,
                "photoDate": photo_date,
                "articleId": article_id,
                "source": "article_body",
            }
        )

    return candidates


def collect_article_gallery_images(articles: list[dict[str, Any]]) -> list[dict]:
    """Compatibilità test: raccoglie copertine e immagini corpo."""
    images: list[dict] = []
    seen: set[str] = set()
    for article in articles:
        for cand in collect_article_gallery_candidates(article):
            url = cand["url"]
            if url in seen:
                continue
            seen.add(url)
            images.append(
                {
                    "id": _gallery_item_id(url),
                    "url": url,
                    "path": url,
                    "caption": cand["caption"],
                    "articleId": cand["articleId"],
                    "source": cand["source"],
                }
            )
    return images


async def list_public_gallery(db) -> list[dict]:
    """Immagini approvate per il carosello in home."""
    from .media_urls import resolve_media_fields

    items = (
        await db.gallery_images.find(
            {"status": "approved"},
            {"_id": 0},
        )
        .sort([("sortOrder", 1), ("createdAt", -1)])
        .to_list(500)
    )
    for item in items:
        resolve_media_fields(item)
    return items


async def _mark_existing_crop_edits(db) -> int:
    """Riconosce ritagli già salvati (url diverso dall'originale) prima del flag cropEdited."""
    marked = 0
    items = await db.gallery_images.find(
        {"cropEdited": {"$ne": True}, "sourceUrl": {"$nin": ["", None]}},
        {"_id": 0, "id": 1, "url": 1, "sourceUrl": 1},
    ).to_list(5000)
    for item in items:
        if _normalize_gallery_url(item.get("url") or "") != _normalize_gallery_url(
            item.get("sourceUrl") or ""
        ):
            await db.gallery_images.update_one(
                {"id": item["id"]},
                {"$set": {"cropEdited": True, "updatedAt": _ts()}},
            )
            marked += 1
    return marked


async def ensure_gallery_metadata(db) -> None:
    """Default aspect/sourceUrl e metadati da articoli collegati."""
    await _mark_existing_crop_edits(db)
    await db.gallery_images.update_many(
        {"aspect": {"$nin": ["16:9", "9:16"]}},
        {"$set": {"aspect": "16:9"}},
    )
    await db.gallery_images.update_many(
        {
            "$or": [
                {"sourceUrl": {"$exists": False}},
                {"sourceUrl": ""},
                {"sourceUrl": None},
            ],
            "cropEdited": {"$ne": True},
        },
        [{"$set": {"sourceUrl": "$url"}}],
    )
    await db.gallery_images.update_many(
        {}, {"$unset": {"focalX": "", "focalY": "", "displayAreas": ""}}
    )

    removed = await dedupe_gallery_images(db)
    if removed:
        logger.info("Galleria: rimosse %s immagini duplicate", removed)

    linked = await db.gallery_images.find(
        {"articleId": {"$nin": ["", None]}},
        {"_id": 0, "id": 1, "articleId": 1, "category": 1, "photoDate": 1},
    ).to_list(5000)

    for img in linked:
        article = await db.articles.find_one(
            {"id": img["articleId"]},
            {"_id": 0, "category": 1, "publishedAt": 1},
        )
        if not article:
            continue
        upd: dict[str, str] = {}
        if (
            not (img.get("category") or "").strip()
            and (article.get("category") or "").strip()
        ):
            upd["category"] = article["category"].strip()
        if not (img.get("photoDate") or "").strip():
            photo_date = _article_photo_date(article)
            if photo_date:
                upd["photoDate"] = photo_date
        if upd:
            upd["updatedAt"] = _ts()
            await db.gallery_images.update_one({"id": img["id"]}, {"$set": upd})

    from .gallery_member_tags import ensure_gallery_member_tags

    await ensure_gallery_member_tags(db)


async def _insert_curated_gallery_image(
    db,
    *,
    curated: dict[str, Any],
    analysis,
    sort_order: int,
) -> None:
    from .gallery_curation import process_gallery_image, save_curated_upload

    source_url = (curated.get("url") or "").strip()
    processed_bytes, aspect = process_gallery_image(analysis.raw_bytes, analysis.aspect)
    rel_path, public_url = save_curated_upload(processed_bytes)

    now = _ts()
    doc = GalleryImage(
        url=public_url,
        path=rel_path,
        sourceUrl=source_url,
        caption=curated.get("caption") or "",
        category=curated.get("category") or "",
        photoDate=curated.get("photoDate") or _today_date(),
        aspect=_normalize_aspect(aspect),
        contentHash=analysis.content_hash,
        phash=format(analysis.phash, "016x"),
        status="approved",
        source=curated.get("source") or "article_body",
        articleId=curated.get("articleId") or "",
        sortOrder=sort_order,
        createdAt=now,
        updatedAt=now,
    ).model_dump()
    await db.gallery_images.insert_one(doc.copy())


async def rebuild_curated_gallery_from_articles(db) -> int:
    """Importa da tutti gli articoli pubblici con selezione automatica."""
    from .gallery_curation import (
        build_dedup_state_from_existing,
        select_curated_candidates,
    )

    articles = (
        await db.articles.find(
            {"status": "published", "portalOnly": {"$ne": True}},
            {
                "_id": 0,
                "id": 1,
                "title": 1,
                "coverUrl": 1,
                "bodyHtml": 1,
                "category": 1,
                "publishedAt": 1,
            },
        )
        .sort("publishedAt", -1)
        .to_list(1000)
    )

    # Mantieni upload admin/associati e ritagli manuali; rigenera solo immagini da articoli non modificate
    preserved = await db.gallery_images.find(
        {
            "$or": [
                {"source": {"$nin": list(ARTICLE_GALLERY_SOURCES)}},
                {"cropEdited": True},
            ]
        },
        {"_id": 0},
    ).to_list(500)
    await db.gallery_images.delete_many(
        {
            "source": {"$in": list(ARTICLE_GALLERY_SOURCES)},
            "cropEdited": {"$ne": True},
        }
    )

    candidates: list[dict[str, Any]] = []
    for article in articles:
        candidates.extend(collect_article_gallery_candidates(article))

    state = build_dedup_state_from_existing(preserved)
    selected = await select_curated_candidates(candidates, state)

    sort_order = 0
    for item in selected:
        await _insert_curated_gallery_image(
            db,
            curated=item.candidate,
            analysis=item.analysis,
            sort_order=sort_order,
        )
        sort_order += 1

    await ensure_gallery_metadata(db)
    from .gallery_member_tags import ensure_gallery_member_tags

    await ensure_gallery_member_tags(db)
    logger.info(
        "Galleria curata: %s immagini da %s articoli (%s candidate analizzate)",
        sort_order,
        len(articles),
        len(candidates),
    )
    return sort_order


async def backfill_gallery_from_articles(db) -> int:
    """Popola/aggiorna gallery_images da articoli con curazione automatica."""
    return await rebuild_curated_gallery_from_articles(db)


async def sync_article_gallery(db, article: dict[str, Any]) -> None:
    """Aggiorna le immagini galleria di un singolo articolo (curate)."""
    from .gallery_curation import (
        analyze_candidate,
        build_dedup_state_from_existing,
        select_curated_candidates,
    )

    article_id = (article.get("id") or "").strip()
    if not article_id:
        return

    await db.gallery_images.delete_many(
        {
            "articleId": article_id,
            "source": {"$in": list(ARTICLE_GALLERY_SOURCES)},
            "cropEdited": {"$ne": True},
        }
    )

    if article.get("portalOnly"):
        return

    others = await db.gallery_images.find(
        {"articleId": {"$ne": article_id}},
        {"_id": 0, "url": 1, "sourceUrl": 1, "contentHash": 1, "phash": 1},
    ).to_list(5000)
    state = build_dedup_state_from_existing(others)

    candidates = collect_article_gallery_candidates(article)
    selected = await select_curated_candidates(
        candidates, state, max_total=MAX_PER_ARTICLE_SYNC
    )

    base_order = await db.gallery_images.count_documents({})
    for idx, item in enumerate(selected):
        await _insert_curated_gallery_image(
            db,
            curated=item.candidate,
            analysis=item.analysis,
            sort_order=base_order + idx,
        )

    from .gallery_member_tags import sync_gallery_member_tags_for_article

    await sync_gallery_member_tags_for_article(db, article)


MAX_PER_ARTICLE_SYNC = 3


async def sync_article_cover_gallery(db, article: dict[str, Any]) -> None:
    await sync_article_gallery(db, article)


async def save_uploaded_gallery_image(
    db,
    *,
    url: str,
    path: str,
    caption: str = "",
    sort_order: int = 0,
    status: str = "approved",
    source: str = "admin",
    member_id: str = "",
    member_name: str = "",
    member_ids: list[str] | None = None,
    category: str = "",
    photo_date: str = "",
    source_url: str = "",
    aspect: str = "16:9",
) -> dict:
    now = _ts()
    if not photo_date:
        photo_date = _today_date()
    display_source = (source_url or url).strip() or url
    doc = GalleryImage(
        url=url,
        path=path or url,
        sourceUrl=display_source,
        caption=caption,
        category=category,
        photoDate=photo_date,
        aspect=_normalize_aspect(aspect),
        sortOrder=sort_order,
        status=status,
        source=source,
        memberId=member_id,
        memberName=member_name,
        memberIds=list(member_ids or []),
        createdAt=now,
        updatedAt=now,
    ).model_dump()
    await db.gallery_images.insert_one(doc.copy())
    return doc
