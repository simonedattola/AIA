"""Selezione automatica immagini galleria da articoli: qualità, dedup, orientamento."""
from __future__ import annotations

import hashlib
import io
import logging
import math
import re
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

MIN_WIDTH = 480
MIN_HEIGHT = 360
MIN_PIXELS = MIN_WIDTH * MIN_HEIGHT
MIN_BYTES = 12_000
MAX_ASPECT_RATIO = 3.2
MAX_BODY_PER_ARTICLE = 2
MAX_COVER_PER_ARTICLE = 1
MAX_GALLERY_TOTAL = 96
PHASH_DISTANCE_THRESHOLD = 10
SKIP_URL_RE = re.compile(
    r"(favicon|icon|logo|avatar|emoji|spacer|1x1|pixel\.|badge|spinner|gravatar|"
    r"placeholder|thumb_?x|\.svg(\?|$)|data:image)",
    re.I,
)


@dataclass
class ImageAnalysis:
    width: int
    height: int
    byte_size: int
    content_hash: str
    phash: int
    aspect: str  # 16:9 | 9:16
    quality_score: float
    raw_bytes: bytes


def _hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def _average_hash(img: Image.Image, size: int = 8) -> int:
    gray = img.convert("L").resize((size, size), Image.Resampling.LANCZOS)
    pixels = list(gray.getdata())
    avg = sum(pixels) / len(pixels)
    bits = 0
    for i, p in enumerate(pixels):
        if p >= avg:
            bits |= 1 << i
    return bits


def _detect_aspect(width: int, height: int) -> str:
    if height > width * 1.08:
        return "9:16"
    return "16:9"


def _quality_score(width: int, height: int, byte_size: int, *, is_cover: bool) -> float:
    pixels = width * height
    score = math.log(max(pixels, 1)) * 12
    score += min(byte_size / 40_000, 18)
    if is_cover:
        score += 30
    ratio = max(width, height) / max(min(width, height), 1)
    if ratio > 2.2:
        score -= 20
    if width < 640 or height < 480:
        score -= 8
    return score


def _should_skip_url(url: str) -> bool:
    u = (url or "").strip().lower()
    if not u or u.startswith("data:"):
        return True
    return bool(SKIP_URL_RE.search(u))


def _analyze_bytes(data: bytes, *, is_cover: bool) -> ImageAnalysis | None:
    if len(data) < MIN_BYTES:
        return None
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)
        width, height = img.size
    except Exception:
        return None

    if width < MIN_WIDTH or height < MIN_HEIGHT or width * height < MIN_PIXELS:
        return None
    ratio = max(width, height) / max(min(width, height), 1)
    if ratio > MAX_ASPECT_RATIO:
        return None

    if img.mode not in ("RGB", "L"):
        rgb = img.convert("RGB")
    else:
        rgb = img.convert("RGB") if img.mode == "L" else img

    content_hash = hashlib.sha256(data).hexdigest()
    phash = _average_hash(rgb)
    aspect = _detect_aspect(width, height)
    return ImageAnalysis(
        width=width,
        height=height,
        byte_size=len(data),
        content_hash=content_hash,
        phash=phash,
        aspect=aspect,
        quality_score=_quality_score(width, height, len(data), is_cover=is_cover),
        raw_bytes=data,
    )


async def load_image_bytes(url: str) -> bytes | None:
    from .media_urls import public_api_base, resolve_media_url

    u = (url or "").strip()
    if not u:
        return None

    def _read_local(name: str) -> bytes | None:
        if not name:
            return None
        from . import storage as upload_storage

        return upload_storage.read_bytes(name)

    if "/api/uploads/" in u:
        data = _read_local(u.split("/")[-1])
        if data:
            return data

    resolved = resolve_media_url(u)
    base = public_api_base()
    if base and resolved.startswith(base) and "/api/uploads/" in resolved:
        data = _read_local(resolved.split("/")[-1])
        if data:
            return data

    if resolved.startswith("http://") or resolved.startswith("https://"):
        try:
            async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
                r = await client.get(resolved)
                r.raise_for_status()
                ctype = (r.headers.get("content-type") or "").lower()
                if "svg" in ctype:
                    return None
                return r.content
        except Exception as exc:
            logger.debug("Galleria: download fallito %s (%s)", resolved[:80], exc)
            return None
    return _read_local(u.split("/")[-1])


def process_gallery_image(data: bytes, aspect: str) -> tuple[bytes, str]:
    """EXIF, ritaglio centrato 16:9 o 9:16, export JPEG."""
    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB",):
        img = img.convert("RGB")

    w, h = img.size
    aspect = _detect_aspect(w, h) if aspect not in ("16:9", "9:16") else aspect
    target = 16 / 9 if aspect == "16:9" else 9 / 16
    current = w / h

    if current > target:
        new_w = int(h * target)
        left = max(0, (w - new_w) // 2)
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target)
        top = max(0, (h - new_h) // 2)
        img = img.crop((0, top, w, top + new_h))

    max_size = (1920, 1080) if aspect == "16:9" else (1080, 1920)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92, optimize=True)
    return buf.getvalue(), aspect


def save_curated_upload(data: bytes) -> tuple[str, str]:
    from . import storage as upload_storage
    from .media_urls import resolve_media_url

    name = f"gallery-curated-{uuid.uuid4().hex[:12]}.jpg"
    rel = upload_storage.save_bytes(name, data, content_type="image/jpeg")
    return rel, resolve_media_url(rel)


@dataclass
class CuratedCandidate:
    candidate: dict[str, Any]
    analysis: ImageAnalysis


@dataclass
class DedupState:
    urls: set[str]
    content_hashes: set[str]
    phashes: list[int]
    per_article_cover: dict[str, int]
    per_article_body: dict[str, int]


def _normalize_url_key(url: str) -> str:
    from .media_urls import resolve_media_url

    u = resolve_media_url((url or "").strip())
    if not u:
        return ""
    if u.startswith("http://") or u.startswith("https://"):
        from urllib.parse import urlparse, urlunparse

        p = urlparse(u)
        return urlunparse((p.scheme, p.netloc, p.path, "", "", "")).lower()
    return u.lower().rstrip("/")


def _is_duplicate(analysis: ImageAnalysis, state: DedupState) -> bool:
    if analysis.content_hash in state.content_hashes:
        return True
    for existing in state.phashes:
        if _hamming(analysis.phash, existing) <= PHASH_DISTANCE_THRESHOLD:
            return True
    return False


def _article_limits_ok(article_id: str, is_cover: bool, state: DedupState) -> bool:
    if not article_id:
        return True
    if is_cover:
        return state.per_article_cover.get(article_id, 0) < MAX_COVER_PER_ARTICLE
    return state.per_article_body.get(article_id, 0) < MAX_BODY_PER_ARTICLE


def _mark_accepted(analysis: ImageAnalysis, url_key: str, article_id: str, is_cover: bool, state: DedupState) -> None:
    state.urls.add(url_key)
    state.content_hashes.add(analysis.content_hash)
    state.phashes.append(analysis.phash)
    if article_id:
        if is_cover:
            state.per_article_cover[article_id] = state.per_article_cover.get(article_id, 0) + 1
        else:
            state.per_article_body[article_id] = state.per_article_body.get(article_id, 0) + 1


def build_dedup_state_from_existing(items: list[dict], *, include_phash: bool = True) -> DedupState:
    state = DedupState(urls=set(), content_hashes=set(), phashes=[], per_article_cover={}, per_article_body={})
    for item in items:
        url_key = _normalize_url_key(item.get("sourceUrl") or item.get("url") or "")
        if url_key:
            state.urls.add(url_key)
        ch = (item.get("contentHash") or "").strip()
        if ch:
            state.content_hashes.add(ch)
        ph = (item.get("phash") or "").strip()
        if include_phash and ph:
            try:
                state.phashes.append(int(ph, 16))
            except ValueError:
                pass
    return state


async def analyze_candidate(candidate: dict[str, Any]) -> CuratedCandidate | None:
    url = (candidate.get("url") or "").strip()
    if _should_skip_url(url):
        return None
    url_key = _normalize_url_key(url)
    if not url_key:
        return None

    data = await load_image_bytes(url)
    if not data:
        return None

    is_cover = candidate.get("source") == "article_cover"
    analysis = _analyze_bytes(data, is_cover=is_cover)
    if not analysis:
        return None

    return CuratedCandidate(candidate=candidate, analysis=analysis)


async def select_curated_candidates(
    candidates: list[dict[str, Any]],
    state: DedupState,
    *,
    max_total: int = MAX_GALLERY_TOTAL,
) -> list[CuratedCandidate]:
    """Ordina per qualità, applica dedup globale e limiti per articolo."""
    analyzed: list[CuratedCandidate] = []
    for cand in candidates:
        url_key = _normalize_url_key(cand.get("url") or "")
        if url_key and url_key in state.urls:
            continue
        item = await analyze_candidate(cand)
        if item:
            analyzed.append(item)

    analyzed.sort(key=lambda x: x.analysis.quality_score, reverse=True)

    selected: list[CuratedCandidate] = []
    for item in analyzed:
        if len(selected) >= max_total:
            break
        cand = item.candidate
        article_id = (cand.get("articleId") or "").strip()
        is_cover = cand.get("source") == "article_cover"
        url_key = _normalize_url_key(cand.get("url") or "")

        if url_key and url_key in state.urls:
            continue
        if not _article_limits_ok(article_id, is_cover, state):
            continue
        if _is_duplicate(item.analysis, state):
            continue

        selected.append(item)
        _mark_accepted(item.analysis, url_key, article_id, is_cover, state)

    return selected
