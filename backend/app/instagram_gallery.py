"""Import immagini da Instagram nel carosello galleria (esclude designazioni e contenuti non adatti)."""
from __future__ import annotations

import base64
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from .gallery import save_uploaded_gallery_image
from .gallery_curation import process_gallery_image, save_curated_upload

logger = logging.getLogger(__name__)

IG_APP_ID = "936619743392459"
DEFAULT_USERNAME = "aia_legnano"
DEFAULT_USER_ID = "19144095477"
SINCE_YEAR_DEFAULT = 2021

_DESIGNATION_PATTERNS = (
    re.compile(r"#designazioni\b", re.I),
    re.compile(r"#convocat", re.I),
    re.compile(r"\bdesignazioni\b", re.I),
    re.compile(r"ecco le (partite|designazioni)", re.I),
    re.compile(r"ultimo (weekend|sforzo).{0,160}(partite|designazioni)", re.I | re.S),
    re.compile(r"buon lavoro a tutti.*#designazioni", re.I | re.S),
    re.compile(r"partite di questo fine settimana", re.I),
    re.compile(r"designazioni del weekend", re.I),
    re.compile(r"si prospetta una domenica tranquilla.*#designazioni", re.I | re.S),
    re.compile(r"ecco le designazioni", re.I),
    re.compile(r"fine settimana.*🔜.*#designazioni", re.I | re.S),
)

_UNSUITABLE_PATTERNS = (
    re.compile(r"#quiztime\b", re.I),
    re.compile(r"\bquiz time\b", re.I),
    re.compile(r"#sondaggi", re.I),
    re.compile(r"sondaggio\b", re.I),
    re.compile(r"#risultati\b.*\bgirone\b", re.I | re.S),
)


def parse_instagram_username(url_or_handle: str) -> str:
    raw = (url_or_handle or "").strip()
    if not raw:
        return DEFAULT_USERNAME
    if raw.startswith("@"):
        return raw[1:].split("/")[0] or DEFAULT_USERNAME
    m = re.search(r"instagram\.com/([^/?#]+)", raw, re.I)
    if m:
        handle = m.group(1).strip("/")
        if handle.lower() in {"p", "reel", "stories", "explore"}:
            return DEFAULT_USERNAME
        return handle
    return raw.split("/")[0] or DEFAULT_USERNAME


def is_designation_post(caption: str) -> bool:
    text = (caption or "").strip()
    if not text:
        return False
    for pat in _DESIGNATION_PATTERNS:
        if pat.search(text):
            return True
    lower = text.lower()
    if "#designazioni" in lower:
        return True
    if "designazioni" in lower and any(k in lower for k in ("weekend", "partite", "girone", "🔜", "fine settimana")):
        return True
    if "buon lavoro a tutti" in lower and ("partite" in lower or "weekend" in lower or "playoff" in lower):
        if "raduno" not in lower and "premiat" not in lower:
            return True
    return False


def is_unsuitable_for_gallery(
    caption: str,
    *,
    media_type: int | None = None,
    product_type: str = "",
) -> bool:
    """Esclude designazioni, reel/video, quiz e contenuti poco adatti al carosello."""
    text = (caption or "").strip()
    if is_designation_post(text):
        return True
    for pat in _UNSUITABLE_PATTERNS:
        if pat.search(text):
            return True
    pt = (product_type or "").lower()
    if pt in {"clips", "igtv"}:
        return True
    if media_type == 2 and pt != "carousel_container":
        return True
    return False


def _ig_headers(session_id: str = "") -> dict[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "X-IG-App-ID": IG_APP_ID,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "*/*",
        "Accept-Language": "it-IT,it;q=0.8,en;q=0.6",
    }
    if session_id:
        headers["Cookie"] = f"sessionid={session_id};"
    return headers


def _caption_from_item(item: dict[str, Any]) -> str:
    cap = item.get("caption")
    if isinstance(cap, dict):
        return (cap.get("text") or "").strip()
    if isinstance(cap, str):
        return cap.strip()
    return ""


def _image_url_from_item(item: dict[str, Any]) -> str:
    media_type = item.get("media_type")
    if media_type == 8:
        children = item.get("carousel_media") or []
        for child in children:
            if child.get("media_type") == 1:
                cands = (child.get("image_versions2") or {}).get("candidates") or []
                if cands:
                    return (cands[0].get("url") or "").strip()
        return ""
    if media_type == 2:
        return ""
    cands = (item.get("image_versions2") or {}).get("candidates") or []
    if cands:
        return (cands[0].get("url") or "").strip()
    return (item.get("display_url") or item.get("thumbnail_src") or "").strip()


def _permalink(_username: str, shortcode: str) -> str:
    return normalize_instagram_permalink(shortcode)


def normalize_instagram_permalink(shortcode_or_url: str) -> str:
    raw = (shortcode_or_url or "").strip().rstrip("/")
    if not raw:
        return ""
    m = re.search(r"instagram\.com/(?:[^/]+/)?p/([A-Za-z0-9_-]+)", raw, re.I)
    code = m.group(1) if m else raw.split("/")[-1]
    return f"https://www.instagram.com/p/{code}/"


def instagram_shortcode_from_url(url: str) -> str:
    norm = normalize_instagram_permalink(url)
    return norm.rstrip("/").split("/")[-1] if norm else ""


def _shortcode_from_item(item: dict[str, Any]) -> str:
    return (item.get("code") or item.get("shortcode") or "").strip()


def _parse_feed_item(item: dict[str, Any], username: str) -> dict[str, Any] | None:
    shortcode = _shortcode_from_item(item)
    if not shortcode:
        return None
    caption = _caption_from_item(item)
    media_type = item.get("media_type")
    product_type = (item.get("product_type") or "").strip()
    if is_unsuitable_for_gallery(caption, media_type=media_type, product_type=product_type):
        return None
    image_url = _image_url_from_item(item)
    if not image_url:
        return None
    taken_at = int(item.get("taken_at") or 0)
    return {
        "shortcode": shortcode,
        "caption": caption,
        "imageUrl": image_url,
        "permalink": _permalink(username, shortcode),
        "takenAt": taken_at,
        "photoDate": datetime.fromtimestamp(taken_at, tz=timezone.utc).strftime("%Y-%m-%d")
        if taken_at
        else "",
    }


def fetch_user_feed_page(
    user_id: str,
    *,
    max_id: str | None = None,
    count: int = 50,
    session_id: str = "",
    username: str = DEFAULT_USERNAME,
) -> tuple[list[dict[str, Any]], str | None, bool]:
    """Una pagina del feed utente Instagram."""
    headers = _ig_headers(session_id)
    headers["Referer"] = f"https://www.instagram.com/{username}/"
    params: dict[str, str | int] = {"count": count}
    if max_id:
        params["max_id"] = max_id

    with httpx.Client(timeout=60, follow_redirects=True) as client:
        r = client.get(
            f"https://www.instagram.com/api/v1/feed/user/{user_id}/",
            headers=headers,
            params=params,
        )
        if r.status_code != 200:
            raise RuntimeError(f"Instagram feed HTTP {r.status_code}")
        data = r.json()

    posts: list[dict[str, Any]] = []
    for item in data.get("items") or []:
        parsed = _parse_feed_item(item, username)
        if parsed:
            posts.append(parsed)

    next_max_id = data.get("next_max_id")
    if next_max_id is not None:
        next_max_id = str(next_max_id)
    more = bool(data.get("more_available"))
    return posts, next_max_id, more


def _image_url_from_instaloader_post(post) -> str:
    node = post._node
    if post.typename == "GraphSidecar":
        for edge in (node.get("edge_sidecar_to_children") or {}).get("edges") or []:
            child = edge.get("node") or {}
            if not child.get("is_video"):
                return (child.get("display_url") or "").strip()
        return ""
    if node.get("is_video"):
        return ""
    return (node.get("display_url") or "").strip()


def fetch_all_profile_posts_instaloader(
    username: str = DEFAULT_USERNAME,
    *,
    session_id: str = "",
    since_year: int = SINCE_YEAR_DEFAULT,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Archivio completo profilo (richiede INSTAGRAM_SESSION_ID valido)."""
    import instaloader

    username = parse_instagram_username(username)
    session_id = session_id or os.getenv("INSTAGRAM_SESSION_ID", "").strip()
    if not session_id:
        raise RuntimeError("INSTAGRAM_SESSION_ID mancante")

    since = datetime(since_year, 1, 1, tzinfo=timezone.utc)
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
    )
    loader.context._session.cookies.set("sessionid", session_id, domain=".instagram.com")
    profile = instaloader.Profile.from_username(loader.context, username)

    posts: list[dict[str, Any]] = []
    stats = {
        "pages": 0,
        "scanned": 0,
        "skippedUnsuitable": 0,
        "skippedOld": 0,
        "skippedNoImage": 0,
    }

    for post in profile.get_posts():
        stats["scanned"] += 1
        if post.date_utc < since:
            stats["skippedOld"] += 1
            break

        caption = post.caption or ""
        product_type = "clips" if post.is_video and post.typename != "GraphSidecar" else ""
        media_type = 2 if post.is_video and post.typename != "GraphSidecar" else 1
        if is_unsuitable_for_gallery(caption, media_type=media_type, product_type=product_type):
            stats["skippedUnsuitable"] += 1
            continue

        image_url = _image_url_from_instaloader_post(post)
        if not image_url:
            stats["skippedNoImage"] += 1
            continue

        taken_at = int(post.date_utc.timestamp())
        posts.append(
            {
                "shortcode": post.shortcode,
                "caption": caption,
                "imageUrl": image_url,
                "permalink": f"https://www.instagram.com/p/{post.shortcode}/",
                "takenAt": taken_at,
                "photoDate": post.date_utc.strftime("%Y-%m-%d"),
            }
        )

    stats["pages"] = 1
    return posts, stats


def fetch_all_profile_posts(
    username: str = DEFAULT_USERNAME,
    *,
    user_id: str = DEFAULT_USER_ID,
    session_id: str = "",
    since_year: int = SINCE_YEAR_DEFAULT,
    max_pages: int = 80,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Tutti i post foto dal since_year (con paginazione)."""
    username = parse_instagram_username(username)
    since_ts = int(datetime(since_year, 1, 1, tzinfo=timezone.utc).timestamp())
    session_id = session_id or os.getenv("INSTAGRAM_SESSION_ID", "").strip()

    if session_id:
        try:
            return fetch_all_profile_posts_instaloader(
                username, session_id=session_id, since_year=since_year
            )
        except Exception as exc:
            logger.warning("Instagram instaloader fallito, uso API feed: %s", exc)

    suitable: list[dict[str, Any]] = []
    stats = {
        "pages": 0,
        "scanned": 0,
        "skippedUnsuitable": 0,
        "skippedOld": 0,
        "skippedNoImage": 0,
    }

    max_id: str | None = None
    stop = False

    with httpx.Client(timeout=60, follow_redirects=True) as client:
        headers = _ig_headers(session_id)
        headers["Referer"] = f"https://www.instagram.com/{username}/"

        for _ in range(max_pages):
            params: dict[str, str | int] = {"count": 50}
            if max_id:
                params["max_id"] = max_id
            r = client.get(
                f"https://www.instagram.com/api/v1/feed/user/{user_id}/",
                headers=headers,
                params=params,
            )
            if r.status_code != 200:
                raise RuntimeError(f"Instagram feed HTTP {r.status_code}")
            data = r.json()
            stats["pages"] += 1

            for item in data.get("items") or []:
                stats["scanned"] += 1
                taken_at = int(item.get("taken_at") or 0)
                if taken_at and taken_at < since_ts:
                    stats["skippedOld"] += 1
                    stop = True
                    continue

                caption = _caption_from_item(item)
                media_type = item.get("media_type")
                product_type = (item.get("product_type") or "").strip()
                if is_unsuitable_for_gallery(caption, media_type=media_type, product_type=product_type):
                    stats["skippedUnsuitable"] += 1
                    continue

                parsed = _parse_feed_item(item, username)
                if not parsed:
                    stats["skippedNoImage"] += 1
                    continue
                suitable.append(parsed)

            if stop or not data.get("more_available"):
                break
            next_id = data.get("next_max_id")
            if not next_id:
                break
            max_id = str(next_id)
            time.sleep(0.35)

    return suitable, stats


def fetch_profile_posts(
    username: str,
    *,
    session_id: str = "",
    limit: int = 36,
    user_id: str = DEFAULT_USER_ID,
    since_year: int = SINCE_YEAR_DEFAULT,
) -> list[dict[str, Any]]:
    """Compat: primi N post oppure tutti se limit<=0."""
    if limit <= 0:
        posts, _ = fetch_all_profile_posts(
            username, user_id=user_id, session_id=session_id, since_year=since_year
        )
        return posts
    posts, _, _ = fetch_user_feed_page(
        user_id, session_id=session_id, username=parse_instagram_username(username)
    )
    since_ts = int(datetime(since_year, 1, 1, tzinfo=timezone.utc).timestamp())
    out = [p for p in posts if (p.get("takenAt") or since_ts) >= since_ts]
    return out[:limit]


def _decode_image_payload(post: dict[str, Any]) -> bytes:
    data_url = (post.get("imageDataUrl") or "").strip()
    if data_url.startswith("data:"):
        _meta, b64 = data_url.split(",", 1)
        return base64.b64decode(b64)

    image_url = (post.get("imageUrl") or post.get("img") or "").strip()
    if not image_url:
        raise ValueError("Nessuna immagine nel post")

    headers = _ig_headers(os.getenv("INSTAGRAM_SESSION_ID", ""))
    headers["Referer"] = "https://www.instagram.com/"
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        r = client.get(image_url, headers=headers)
        r.raise_for_status()
        return r.content


def _caption_for_gallery(caption: str) -> str:
    line = (caption or "").strip().split("\n", 1)[0].strip()
    if len(line) > 180:
        return f"{line[:177]}…"
    return line


async def import_instagram_post(
    db,
    post: dict[str, Any],
    *,
    sort_order: int,
    username: str = DEFAULT_USERNAME,
) -> dict[str, Any] | None:
    caption = (post.get("caption") or post.get("alt") or "").strip()
    media_type = post.get("mediaType")
    product_type = (post.get("productType") or "").strip()
    if is_unsuitable_for_gallery(caption, media_type=media_type, product_type=product_type):
        return None

    permalink = (post.get("permalink") or post.get("href") or "").strip()
    if not permalink:
        shortcode = (post.get("shortcode") or "").strip()
        if shortcode:
            permalink = _permalink(parse_instagram_username(username), shortcode)
    if permalink:
        permalink = normalize_instagram_permalink(permalink)
        code = instagram_shortcode_from_url(permalink)
        existing = await db.gallery_images.find_one(
            {
                "source": "instagram",
                "$or": [
                    {"sourceUrl": permalink},
                    {"sourceUrl": {"$regex": f"/p/{re.escape(code)}/?$", "$options": "i"}},
                ],
            },
            {"_id": 0, "id": 1},
        )
        if existing:
            return None

    try:
        raw = _decode_image_payload(post)
    except Exception as exc:
        logger.warning("Instagram: download fallito %s — %s", permalink or caption[:40], exc)
        return None

    processed, aspect = process_gallery_image(raw, "16:9")
    rel_path, public_url = save_curated_upload(processed)
    now = datetime.now(timezone.utc).isoformat()
    photo_date = (post.get("photoDate") or "").strip() or now[:10]

    doc = await save_uploaded_gallery_image(
        db,
        url=public_url,
        path=rel_path,
        source_url=permalink or public_url,
        caption=_caption_for_gallery(caption) or "Instagram AIA Legnano",
        category="Instagram",
        photo_date=photo_date,
        aspect=aspect,
        sort_order=sort_order,
        status="approved",
        source="instagram",
    )
    doc["updatedAt"] = now
    await db.gallery_images.update_one({"id": doc["id"]}, {"$set": {"updatedAt": now}})
    return doc


async def sync_instagram_gallery(
    db,
    *,
    username: str = DEFAULT_USERNAME,
    user_id: str = DEFAULT_USER_ID,
    session_id: str = "",
    since_year: int = SINCE_YEAR_DEFAULT,
    limit: int = 0,
    posts: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    """Importa post Instagram nel carosello."""
    fetch_stats: dict[str, int] = {}
    if posts is None:
        session_id = session_id or os.getenv("INSTAGRAM_SESSION_ID", "").strip()
        if limit > 0:
            posts = fetch_profile_posts(
                username, session_id=session_id, limit=limit, user_id=user_id, since_year=since_year
            )
        else:
            posts, fetch_stats = fetch_all_profile_posts(
                username, user_id=user_id, session_id=session_id, since_year=since_year
            )

    base_order = await db.gallery_images.count_documents({})
    added = 0
    skipped_unsuitable = 0
    skipped_existing = 0
    failed = 0

    for post in posts:
        caption = (post.get("caption") or post.get("alt") or "").strip()
        if is_unsuitable_for_gallery(
            caption,
            media_type=post.get("mediaType"),
            product_type=post.get("productType") or "",
        ):
            skipped_unsuitable += 1
            continue
        permalink = normalize_instagram_permalink(
            (post.get("permalink") or post.get("href") or post.get("shortcode") or "").strip()
        )
        if permalink:
            code = instagram_shortcode_from_url(permalink)
            if await db.gallery_images.find_one(
                {
                    "source": "instagram",
                    "$or": [
                        {"sourceUrl": permalink},
                        {"sourceUrl": {"$regex": f"/p/{re.escape(code)}/?$", "$options": "i"}},
                    ],
                },
                {"_id": 0, "id": 1},
            ):
                skipped_existing += 1
                continue
        try:
            doc = await import_instagram_post(db, post, sort_order=base_order + added)
            if doc:
                added += 1
            elif is_unsuitable_for_gallery(caption):
                skipped_unsuitable += 1
            else:
                skipped_existing += 1
        except Exception:
            failed += 1

    logger.info(
        "Instagram galleria: +%s (saltati %s, già presenti %s, errori %s, scansionati %s)",
        added,
        skipped_unsuitable,
        skipped_existing,
        failed,
        len(posts),
    )
    result = {
        "added": added,
        "skippedUnsuitable": skipped_unsuitable,
        "skippedDesignazioni": skipped_unsuitable,
        "skippedExisting": skipped_existing,
        "failed": failed,
        "scanned": len(posts),
    }
    result.update(fetch_stats)
    return result


async def import_instagram_batch(
    db,
    items: list[dict[str, Any]],
    *,
    username: str = DEFAULT_USERNAME,
) -> dict[str, int]:
    """Import batch (es. da browser con imageDataUrl base64)."""
    return await sync_instagram_gallery(db, username=username, posts=items)


def load_manifest_posts(path: str) -> list[dict[str, Any]]:
    import json
    from pathlib import Path

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "result" in raw:
        inner = raw["result"]
        if isinstance(inner, dict):
            raw = inner.get("value") or inner
    if isinstance(raw, dict) and "posts" in raw:
        return raw["posts"]
    if isinstance(raw, list):
        return raw
    raise ValueError("Formato manifest Instagram non valido")
