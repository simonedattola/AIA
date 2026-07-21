"""Resolve uploaded media paths to absolute URLs for browsers."""
import os
import re
from pathlib import Path
from urllib.parse import urlparse

from .paths import UPLOAD_DIR

_UPLOAD_PATH_RE = re.compile(r"^/api/uploads/")
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def format_file_size_label(size: int) -> str:
    if not size or size <= 0:
        return ""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def upload_basename(url: str | None) -> str | None:
    if not url or not str(url).strip():
        return None
    raw = str(url).strip().split("?")[0]
    if "/api/uploads/" in raw:
        name = raw.split("/api/uploads/")[-1].strip("/")
        return name or None
    return None


def file_size_label_for_media_url(url: str | None) -> str:
    name = upload_basename(url)
    if not name:
        return ""
    path = UPLOAD_DIR / name
    if not path.is_file():
        return ""
    return format_file_size_label(path.stat().st_size)


def public_api_base() -> str:
    return (os.environ.get("PUBLIC_API_URL") or os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")


def _local_absolute_upload_path(url: str) -> str | None:
    """If url is an absolute localhost upload URL, return its path (/api/uploads/...)."""
    try:
        parsed = urlparse(url)
    except Exception:
        return None
    if parsed.scheme not in ("http", "https"):
        return None
    host = (parsed.hostname or "").lower()
    if host not in _LOCAL_HOSTS:
        return None
    path = parsed.path or ""
    if path.startswith("/api/uploads/") or path.startswith("/uploads/"):
        return path if path.startswith("/api/") else f"/api{path}"
    return None


def resolve_media_url(url: str | None) -> str:
    if not url or not str(url).strip():
        return ""
    url = str(url).strip()
    base = public_api_base()
    local_path = _local_absolute_upload_path(url)
    if local_path:
        return f"{base}{local_path}" if base else local_path
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if not base:
        return url
    if url.startswith("/"):
        return f"{base}{url}"
    if _UPLOAD_PATH_RE.match(url) or url.startswith("uploads/"):
        path = url if url.startswith("/") else f"/api/{url.lstrip('/')}"
        if not path.startswith("/api/"):
            path = f"/api/uploads/{url.split('/')[-1]}"
        return f"{base}{path}"
    return url


def resolve_attachments(items: list | None) -> list:
    if not items:
        return []
    out = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        att = dict(raw)
        if att.get("fileUrl"):
            att["fileUrl"] = resolve_media_url(att["fileUrl"])
        out.append(att)
    return out


def resolve_media_fields(doc: dict, fields: tuple[str, ...] = ("photoUrl", "coverUrl", "url")) -> dict:
    for key in fields:
        if key in doc and doc[key]:
            doc[key] = resolve_media_url(doc[key])
    if "bioHtml" in doc and doc.get("bioHtml"):
        doc["bioHtml"] = resolve_html_media_urls(doc["bioHtml"])
    if "bodyHtml" in doc and doc.get("bodyHtml"):
        doc["bodyHtml"] = resolve_html_media_urls(doc["bodyHtml"])
    if "images" in doc and isinstance(doc["images"], list):
        for img in doc["images"]:
            if isinstance(img, dict) and img.get("url"):
                img["url"] = resolve_media_url(img["url"])
    if "attachments" in doc and isinstance(doc["attachments"], list):
        doc["attachments"] = resolve_attachments(doc["attachments"])
    return doc


def resolve_html_media_urls(html: str) -> str:
    base = public_api_base()
    if not base or not html:
        return html or ""

    def repl_src(match):
        return f'{match.group(1)}{base}{match.group(2)}{match.group(3)}'

    html = re.sub(
        r'(src=["\'])(/api/uploads/[^"\']+)(["\'])',
        repl_src,
        html,
    )
    return re.sub(
        r'(href=["\'])(/api/uploads/[^"\']+)(["\'])',
        repl_src,
        html,
    )
