"""Upload storage adapter: local disk (default) or S3/R2."""
from __future__ import annotations

import logging
import mimetypes
from pathlib import Path

from .paths import (
    S3_BUCKET,
    S3_PUBLIC_BASE_URL,
    UPLOAD_DIR,
    object_key,
    s3_client,
    use_object_storage,
)

logger = logging.getLogger(__name__)


def ensure_local_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def save_bytes(name: str, data: bytes, content_type: str | None = None) -> str:
    """Persist file bytes; return public relative path `/api/uploads/{name}`."""
    if use_object_storage():
        ctype = content_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
        client = s3_client()
        extra = {"ContentType": ctype}
        client.put_object(Bucket=S3_BUCKET, Key=object_key(name), Body=data, **extra)
        return f"/api/uploads/{name}"

    ensure_local_dir()
    target = UPLOAD_DIR / name
    target.write_bytes(data)
    return f"/api/uploads/{name}"


def save_fileobj(name: str, fileobj, content_type: str | None = None) -> str:
    """Persist an open binary file object (e.g. UploadFile.file)."""
    data = fileobj.read()
    if isinstance(data, str):
        data = data.encode("utf-8")
    return save_bytes(name, data, content_type=content_type)


def delete(name: str) -> None:
    if not name:
        return
    if use_object_storage():
        try:
            s3_client().delete_object(Bucket=S3_BUCKET, Key=object_key(name))
        except Exception as exc:
            logger.warning("S3 delete failed for %s: %s", name, exc)
        return
    path = UPLOAD_DIR / name
    path.unlink(missing_ok=True)


def exists(name: str) -> bool:
    if not name:
        return False
    if use_object_storage():
        try:
            s3_client().head_object(Bucket=S3_BUCKET, Key=object_key(name))
            return True
        except Exception:
            return False
    return (UPLOAD_DIR / name).is_file()


def read_bytes(name: str) -> bytes | None:
    if not name:
        return None
    if use_object_storage():
        try:
            obj = s3_client().get_object(Bucket=S3_BUCKET, Key=object_key(name))
            return obj["Body"].read()
        except Exception as exc:
            logger.debug("S3 get failed for %s: %s", name, exc)
            return None
    path = UPLOAD_DIR / name
    if path.is_file():
        return path.read_bytes()
    return None


def size_bytes(name: str) -> int | None:
    if not name:
        return None
    if use_object_storage():
        try:
            meta = s3_client().head_object(Bucket=S3_BUCKET, Key=object_key(name))
            return int(meta.get("ContentLength") or 0) or None
        except Exception:
            return None
    path = UPLOAD_DIR / name
    if path.is_file():
        return path.stat().st_size
    return None


def local_path(name: str) -> Path | None:
    """Filesystem path when using local storage; None for object storage."""
    if use_object_storage() or not name:
        return None
    path = UPLOAD_DIR / name
    return path if path.is_file() else None


def public_cdn_url(name: str) -> str | None:
    """Absolute CDN URL when S3_PUBLIC_BASE_URL is configured."""
    if not name or not S3_PUBLIC_BASE_URL:
        return None
    key = object_key(name)
    return f"{S3_PUBLIC_BASE_URL}/{key}"
