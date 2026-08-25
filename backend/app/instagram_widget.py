"""Dati profilo + griglia post per il widget Instagram in home."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
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
WIDGET_CACHE_ID = "instagram-widget-cache"

# Instagram blocca spesso UA browser da IP datacenter (401).
# L'UA client Android ufficiale continua a ricevere il feed pubblico.
_IG_MOBILE_UA = (
    "Instagram 192.0.0.37.107 Android "
    "(33/13; 420dpi; 1080x2400; Google/google; Pixel 7; panther; panther; en_US; 458229257)"
)
_IG_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _ig_headers(*, mobile: bool = True, session_id: str = "") -> dict[str, str]:
    headers = {
        "User-Agent": _IG_MOBILE_UA if mobile else _IG_BROWSER_UA,
        "X-IG-App-ID": IG_APP_ID,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "*/*",
        "Accept-Language": "it-IT,it;q=0.8,en;q=0.6",
    }
    if session_id:
        headers["Cookie"] = f"sessionid={session_id};"
    return headers


def stable_instagram_media_url(shortcode: str, *, size: str = "l") -> str:
    """URL thumbnail via proxy locale (Instagram /media/ non è affidabile nel browser)."""
    code = (shortcode or "").strip()
    if not code:
        return ""
    safe = "".join(ch for ch in code if ch.isalnum() or ch in "_-")
    if not safe:
        return ""
    sz = size if size in {"t", "m", "l"} else "l"
    return f"/api/public/instagram/media/{safe}?size={sz}"


def fetch_instagram_media_bytes(
    shortcode: str, *, size: str = "l"
) -> tuple[bytes, str]:
    """Scarica thumbnail post (JPEG) da Instagram lato server."""
    code = "".join(ch for ch in (shortcode or "") if ch.isalnum() or ch in "_-")
    if not code:
        raise ValueError("shortcode non valido")
    sz = size if size in {"t", "m", "l"} else "l"
    url = f"https://www.instagram.com/p/{code}/media/?size={sz}"
    headers = {
        "User-Agent": _IG_BROWSER_UA,
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Referer": "https://www.instagram.com/",
    }
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        r = client.get(url, headers=headers)
        if r.status_code != 200:
            raise RuntimeError(f"Instagram media HTTP {r.status_code}")
        ctype = (r.headers.get("content-type") or "image/jpeg").split(";")[0].strip()
        if not ctype.startswith("image/"):
            raise RuntimeError("Instagram media non-image")
        return r.content, ctype


def _thumbnail_from_item(item: dict[str, Any]) -> str:
    shortcode = _shortcode_from_item(item)
    # Preferisci URL stabile: i CDN Instagram scadono e rompono la griglia in cache.
    if shortcode:
        return stable_instagram_media_url(shortcode)
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


def _parse_feed_response(
    data: dict[str, Any], username: str, *, limit: int
) -> dict[str, Any]:
    ig_user = data.get("user") or {}
    posts: list[dict[str, Any]] = []
    for item in data.get("items") or []:
        parsed = _widget_post_from_item(item, username)
        if parsed:
            posts.append(parsed)
        if len(posts) >= limit:
            break

    full_name = (ig_user.get("full_name") or username.replace("_", " ")).strip()
    return {
        "profile": {
            "username": ig_user.get("username") or username,
            "fullName": full_name,
            "profilePicUrl": (ig_user.get("profile_pic_url") or "").strip(),
            "isVerified": bool(ig_user.get("is_verified")),
            "profileUrl": f"https://www.instagram.com/{username}/",
        },
        "posts": posts,
    }


def fetch_instagram_widget_sync(
    username: str,
    *,
    user_id: str = DEFAULT_USER_ID,
    limit: int = 12,
    session_id: str = "",
) -> dict[str, Any]:
    """Profilo + post recenti (feed pubblico Instagram)."""
    user = parse_instagram_username(username)
    profile_url = f"https://www.instagram.com/{user}/"
    session_id = session_id or os.getenv("INSTAGRAM_SESSION_ID", "").strip()
    count = max(4, min(limit, 24))
    feed_url = f"https://i.instagram.com/api/v1/feed/user/{user_id}/"
    feed_url_www = f"https://www.instagram.com/api/v1/feed/user/{user_id}/"
    last_error: Exception | None = None

    attempts: list[tuple[str, dict[str, str], bool]] = [
        # (url, headers, warm_cookies)
        (feed_url, _ig_headers(mobile=True, session_id=session_id), False),
        (feed_url_www, _ig_headers(mobile=True, session_id=session_id), False),
        (feed_url_www, _ig_headers(mobile=False, session_id=session_id), True),
    ]

    with httpx.Client(timeout=30, follow_redirects=True) as client:
        for url, headers, warm in attempts:
            try:
                headers = dict(headers)
                headers["Referer"] = profile_url
                if warm:
                    client.get(
                        profile_url,
                        headers={"User-Agent": _IG_BROWSER_UA, "Accept": "text/html"},
                    )
                r = client.get(url, headers=headers, params={"count": count})
                if r.status_code != 200:
                    last_error = RuntimeError(f"Instagram feed HTTP {r.status_code}")
                    continue
                ctype = (r.headers.get("content-type") or "").lower()
                if "json" not in ctype:
                    last_error = RuntimeError("Instagram feed non-JSON")
                    continue
                data = r.json()
                if not isinstance(data, dict) or not (
                    data.get("items") or data.get("user")
                ):
                    last_error = RuntimeError("Instagram feed vuoto/inesatto")
                    continue
                parsed = _parse_feed_response(data, user, limit=limit)
                if not parsed["posts"]:
                    last_error = RuntimeError("Instagram feed senza post utilizzabili")
                    continue
                return parsed
            except Exception as exc:  # noqa: BLE001 — prova tentativo successivo
                last_error = exc
                continue

    raise RuntimeError(f"Instagram feed non disponibile ({last_error or 'unknown'})")


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


async def load_widget_cache(db) -> dict[str, Any] | None:
    doc = await db.site_settings.find_one(
        {"id": WIDGET_CACHE_ID},
        {"_id": 0, "profile": 1, "posts": 1, "updatedAt": 1, "username": 1},
    )
    if not doc:
        return None
    posts = doc.get("posts") or []
    if not posts:
        return None
    normalized: list[dict[str, Any]] = []
    for post in posts:
        p = dict(post)
        code = (p.get("shortcode") or "").strip()
        if code:
            p["imageUrl"] = stable_instagram_media_url(code)
        normalized.append(p)
    return {
        "profile": doc.get("profile") or {},
        "posts": normalized,
        "cachedAt": doc.get("updatedAt"),
        "fromCache": True,
    }


async def save_widget_cache(db, username: str, payload: dict[str, Any]) -> None:
    posts = payload.get("posts") or []
    if not posts:
        return
    # Normalizza imageUrl su URL media stabili quando c'è lo shortcode.
    normalized: list[dict[str, Any]] = []
    for post in posts[:24]:
        p = dict(post)
        code = (p.get("shortcode") or "").strip()
        if code:
            p["imageUrl"] = stable_instagram_media_url(code)
            if not p.get("permalink"):
                p["permalink"] = normalize_instagram_permalink(code)
        normalized.append(p)
    now = datetime.now(timezone.utc).isoformat()
    await db.site_settings.update_one(
        {"id": WIDGET_CACHE_ID},
        {
            "$set": {
                "id": WIDGET_CACHE_ID,
                "username": parse_instagram_username(username),
                "profile": payload.get("profile") or {},
                "posts": normalized,
                "updatedAt": now,
            }
        },
        upsert=True,
    )


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
    """Con cache breve in-process; stats opzionali da CMS (posts/followers/following)."""
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
    """Feed live + fallback cache Mongo / galleria Instagram (mai foto del sito)."""
    gallery = await gallery_instagram_posts(db, limit=limit)
    data = await get_instagram_widget_data(username, limit=limit, stats=stats)
    live_posts = data.get("posts") or []

    if live_posts:
        try:
            await save_widget_cache(db, username, data)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Widget Instagram: salvataggio cache fallito (%s)", exc)

    cached = None
    if not live_posts:
        cached = await load_widget_cache(db)

    sources: list[list[dict[str, Any]]] = [live_posts]
    if cached and cached.get("posts"):
        sources.append(cached["posts"])
        if not data.get("profile") or not (data["profile"].get("profilePicUrl")):
            data["profile"] = cached.get("profile") or data.get("profile") or {}
        data["fromCache"] = True
    sources.append(gallery)

    merged: list[dict[str, Any]] = []
    for group in sources:
        merged = _merge_posts(merged, group, limit=limit)
        if len(merged) >= limit:
            break
    data["posts"] = merged

    if data.get("error") and data["posts"]:
        data.pop("error", None)
    return data
