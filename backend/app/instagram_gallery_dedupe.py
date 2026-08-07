"""Rimuove duplicati galleria Instagram (permalink con/senza username nel path)."""

from __future__ import annotations

from .instagram_gallery import (
    instagram_shortcode_from_url,
    normalize_instagram_permalink,
)


async def dedupe_instagram_gallery(db) -> int:
    items = await db.gallery_images.find({"source": "instagram"}, {"_id": 0}).to_list(
        5000
    )
    by_code: dict[str, list] = {}
    for item in items:
        code = instagram_shortcode_from_url(item.get("sourceUrl") or "")
        if not code:
            continue
        by_code.setdefault(code, []).append(item)

    removed = 0
    for code, group in by_code.items():
        if len(group) < 2:
            canon = normalize_instagram_permalink(code)
            if group[0].get("sourceUrl") != canon:
                await db.gallery_images.update_one(
                    {"id": group[0]["id"]},
                    {"$set": {"sourceUrl": canon}},
                )
            continue
        group.sort(
            key=lambda x: (
                (
                    0
                    if "/p/" in (x.get("sourceUrl") or "")
                    and x["sourceUrl"].count("/") <= 5
                    else 1
                ),
                x.get("createdAt") or "",
            )
        )
        keep = group[0]
        canon = normalize_instagram_permalink(code)
        await db.gallery_images.update_one(
            {"id": keep["id"]},
            {"$set": {"sourceUrl": canon}},
        )
        for dup in group[1:]:
            await db.gallery_images.delete_one({"id": dup["id"]})
            removed += 1
    return removed
