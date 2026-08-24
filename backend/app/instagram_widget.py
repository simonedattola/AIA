"""Dati profilo + griglia post per il widget Instagram in home."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from .instagram_gallery import (
    DEFAULT_USER_ID,
    IG_APP_ID,
    _caption_from_item,
    _image_url_from_item,
    _shortcode_from_item,
    normalize_instagram_permalink,
    parse_instagram_username,
)

logger = logging.getLogger(__name__)

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL_SEC = 300


def _ig_headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "X-IG-App-ID": IG_APP_ID,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "*/*",
        "Accept-Language": "it-IT,it;q=0.8,en;q=0.6",
    }


def _thumbnail_from_item(item: dict[str, Any]) -> str:
    url = _image_url_from_item(item)
    if url:
        return url
    media_type = item.get("media_type")
    if media_type in (2, 8):
        cands = (item.get("image_versions2") or {}).get("candidates") or []
        if cands:
            return (cands[0].get("url") or "").strip()
    return (item.get("thumbnail_url") or item.get("display_url") or "").strip()


def _widget_post_from_item(
    item: dict[str, Any], username: str
) -> dict[str, Any] | None:
    shortcode = _shortcode_from_item(item)
    if not shortcode:
        return None
    thumb = _thumbnail_from_item(item)
    if not thumb:
        return None
    media_type = int(item.get("media_type") or 0)
    product_type = (item.get("product_type") or "").strip().lower()
    is_video = media_type == 2 and product_type not in ("carousel_container",)
    is_carousel = media_type == 8 or product_type == "carousel_container"
    permalink = normalize_instagram_permalink(shortcode)
    return {
        "shortcode": shortcode,
        "permalink": permalink,
        "imageUrl": thumb,
        "caption": _caption_from_item(item)[:120],
        "isVideo": is_video,
        "isCarousel": is_carousel,
    }


def fetch_instagram_widget_sync(
    username: str,
    *,
    user_id: str = DEFAULT_USER_ID,
    limit: int = 12,
) -> dict[str, Any]:
    """Profilo + post recenti (API feed pubblica Instagram)."""
    user = parse_instagram_username(username)
    profile_url = f"https://www.instagram.com/{user}/"
    headers = _ig_headers()
    headers["Referer"] = profile_url

    with httpx.Client(timeout=30, follow_redirects=True) as client:
        r = client.get(
            f"https://www.instagram.com/api/v1/feed/user/{user_id}/",
            headers=headers,
            params={"count": max(4, min(limit, 24))},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Instagram feed HTTP {r.status_code}")
        data = r.json()

    ig_user = data.get("user") or {}
    posts: list[dict[str, Any]] = []
    for item in data.get("items") or []:
        parsed = _widget_post_from_item(item, user)
        if parsed:
            posts.append(parsed)
        if len(posts) >= limit:
            break

    full_name = (ig_user.get("full_name") or user.replace("_", " ")).strip()
    return {
        "profile": {
            "username": ig_user.get("username") or user,
            "fullName": full_name,
            "profilePicUrl": (ig_user.get("profile_pic_url") or "").strip(),
            "isVerified": bool(ig_user.get("is_verified")),
            "profileUrl": profile_url,
        },
        "posts": posts,
    }


async def gallery_instagram_posts(db, *, limit: int = 12) -> list[dict[str, Any]]:
    """Post dal carosello sincronizzato (affidabile anche se l'API live fallisce)."""
    from .media_urls import resolve_media_fields
    from .instagram_gallery import instagram_shortcode_from_url

    items = (
        await db.gallery_images.find(
            {"source": "instagram", "status": "approved"},
            {"_id": 0, "id": 1, "url": 1, "path": 1, "sourceUrl": 1, "caption": 1},
        )
        .sort([("sortOrder", 1), ("createdAt", -1)])
        .to_list(max(4, min(limit, 24)))
    )
    posts: list[dict[str, Any]] = []
    for item in items:
        resolve_media_fields(item)
        image_url = (item.get("url") or item.get("path") or "").strip()
        if not image_url:
            continue
        source_url = (item.get("sourceUrl") or "").strip()
        code = instagram_shortcode_from_url(source_url) or item.get("id") or ""
        posts.append(
            {
                "shortcode": code,
                "permalink": source_url,
                "imageUrl": image_url,
                "caption": (item.get("caption") or "")[:120],
                "isVideo": False,
                "isCarousel": False,
            }
        )
    return posts


def _merge_posts(
    live: list[dict[str, Any]], gallery: list[dict[str, Any]], *, limit: int
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for group in (live, gallery):
        for post in group:
            key = (
                post.get("shortcode")
                or post.get("permalink")
                or post.get("imageUrl")
                or ""
            ).strip()
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(post)
            if len(merged) >= limit:
                return merged
    return merged


async def get_instagram_widget_data(
    username: str,
    *,
    user_id: str = DEFAULT_USER_ID,
    limit: int = 12,
    stats: dict[str, int | None] | None = None,
) -> dict[str, Any]:
    """Con cache breve; stats opzionali da CMS (posts/followers/following)."""
    cache_key = f"{parse_instagram_username(username)}:{limit}"
    now = time.time()
    cached = _CACHE.get(cache_key)
    if cached and now - cached[0] < _CACHE_TTL_SEC:
        payload = dict(cached[1])
    else:
        try:
            payload = await asyncio.to_thread(
                fetch_instagram_widget_sync,
                username,
                user_id=user_id,
                limit=limit,
            )
            _CACHE[cache_key] = (now, payload)
        except Exception as exc:
            logger.warning("Widget Instagram: feed non disponibile (%s)", exc)
            user = parse_instagram_username(username)
            payload = {
                "profile": {
                    "username": user,
                    "fullName": user.replace("_", " ").title(),
                    "profilePicUrl": "",
                    "isVerified": False,
                    "profileUrl": f"https://www.instagram.com/{user}/",
                },
                "posts": [],
                "error": str(exc),
            }

    merged_stats = {
        "posts": None,
        "followers": None,
        "following": None,
    }
    if stats:
        for key in merged_stats:
            val = stats.get(key)
            if isinstance(val, int) and val >= 0:
                merged_stats[key] = val
    if merged_stats["posts"] is None and payload.get("posts"):
        merged_stats["posts"] = len(payload["posts"])

    out = dict(payload)
    out["stats"] = merged_stats
    return out


async def build_instagram_widget_payload(
    db,
    username: str,
    *,
    limit: int = 12,
    stats: dict[str, int | None] | None = None,
) -> dict[str, Any]:
    """Feed live + fallback galleria sincronizzata."""
    gallery = await gallery_instagram_posts(db, limit=limit)
    data = await get_instagram_widget_data(username, limit=limit, stats=stats)
    live_posts = data.get("posts") or []
    data["posts"] = _merge_posts(live_posts, gallery, limit=limit)
    if not data["posts"] and gallery:
        data["posts"] = gallery[:limit]
    if data.get("error") and data["posts"]:
        data.pop("error", None)
    return data
