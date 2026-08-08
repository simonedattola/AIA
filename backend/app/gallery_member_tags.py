"""Tag automatici associati sulle immagini galleria da articoli/notizie."""

from __future__ import annotations

import logging
from typing import Any

from .article_member_match import match_members_by_full_name
from .gallery import _ts

logger = logging.getLogger(__name__)


def merge_member_ids(existing: list[str] | None, extra: list[str] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for mid in list(existing or []) + list(extra or []):
        if not mid or mid in seen:
            continue
        seen.add(mid)
        out.append(mid)
    return out


def member_ids_for_article(article: dict[str, Any], members: list[dict]) -> list[str]:
    """ID associati citati nell'articolo (relatedMemberIds + match nome cognome)."""
    matched = match_members_by_full_name(
        article.get("title") or "",
        article.get("bodyHtml") or "",
        members,
        excerpt=article.get("excerpt") or "",
    )
    return merge_member_ids(article.get("relatedMemberIds"), matched)


async def load_members_for_match(db) -> list[dict]:
    return await db.members.find(
        {},
        {"_id": 0, "id": 1, "firstName": 1, "lastName": 1},
    ).to_list(500)


async def sync_gallery_member_tags_for_article(
    db,
    article: dict[str, Any],
    *,
    members: list[dict] | None = None,
) -> int:
    """Allinea memberIds sulle immagini collegate a un articolo."""
    article_id = (article.get("id") or "").strip()
    if not article_id:
        return 0
    if members is None:
        members = await load_members_for_match(db)
    target_ids = member_ids_for_article(article, members)
    if not target_ids:
        return 0

    ts = _ts()
    updated = 0
    images = await db.gallery_images.find(
        {"articleId": article_id},
        {"_id": 0, "id": 1, "memberIds": 1},
    ).to_list(500)
    for img in images:
        merged = merge_member_ids(img.get("memberIds"), target_ids)
        if merged != (img.get("memberIds") or []):
            await db.gallery_images.update_one(
                {"id": img["id"]},
                {"$set": {"memberIds": merged, "updatedAt": ts}},
            )
            updated += 1
    return updated


async def ensure_gallery_member_tags(db) -> int:
    """Backfill tag associati su tutte le immagini da articoli."""
    members = await load_members_for_match(db)
    if not members:
        return 0

    articles = await db.articles.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "title": 1,
            "excerpt": 1,
            "bodyHtml": 1,
            "relatedMemberIds": 1,
        },
    ).to_list(5000)
    by_id = {a["id"]: a for a in articles if a.get("id")}

    ts = _ts()
    updated = 0
    images = await db.gallery_images.find(
        {"articleId": {"$nin": ["", None]}},
        {"_id": 0, "id": 1, "articleId": 1, "memberIds": 1},
    ).to_list(5000)

    for img in images:
        art = by_id.get(img.get("articleId") or "")
        if not art:
            continue
        target_ids = member_ids_for_article(art, members)
        if not target_ids:
            continue
        merged = merge_member_ids(img.get("memberIds"), target_ids)
        if merged != (img.get("memberIds") or []):
            await db.gallery_images.update_one(
                {"id": img["id"]},
                {"$set": {"memberIds": merged, "updatedAt": ts}},
            )
            updated += 1

    if updated:
        logger.info("Galleria: tag associati aggiornati su %s immagini", updated)
    return updated
