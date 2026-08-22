"""Upload storage adapter: local disk, MongoDB GridFS (Atlas), or S3/R2."""

from __future__ import annotations

import logging
import mimetypes
import os
from pathlib import Path

from .paths import (
    UPLOAD_DIR,
    object_key,
    s3_client,
    use_gridfs,
    use_object_storage,
)

logger = logging.getLogger(__name__)

_gridfs = None
_gridfs_client = None


def ensure_local_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def _fs():
    """Sync GridFS handle on the app MongoDB (persists across Railway deploys)."""
    global _gridfs, _gridfs_client
    if _gridfs is not None:
        return _gridfs
    from gridfs import GridFS
    from pymongo import MongoClient

    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ.get("DB_NAME") or "aia_legnano"
    _gridfs_client = MongoClient(mongo_url)
    _gridfs = GridFS(_gridfs_client[db_name], collection="uploads")
    return _gridfs


def _gridfs_delete(name: str) -> None:
    fs = _fs()
    for doc in fs.find({"filename": name}):
        try:
            fs.delete(doc._id)
        except Exception as exc:
            logger.warning("GridFS delete failed for %s: %s", name, exc)


def _gridfs_put(name: str, data: bytes, content_type: str | None) -> None:
    fs = _fs()
    _gridfs_delete(name)
    ctype = content_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
    fs.put(data, filename=name, contentType=ctype)


def _gridfs_get(name: str) -> bytes | None:
    fs = _fs()
    try:
        return fs.get_last_version(name).read()
    except Exception:
        return None


def _gridfs_exists(name: str) -> bool:
    return bool(_fs().exists({"filename": name}))


def _gridfs_size(name: str) -> int | None:
    fs = _fs()
    try:
        return int(fs.get_last_version(name).length)
    except Exception:
        return None


def save_bytes(name: str, data: bytes, content_type: str | None = None) -> str:
    """Persist file bytes; return public relative path `/api/uploads/{name}`."""
    if use_object_storage():
        from .paths import _s3_bucket

        ctype = (
            content_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
        )
        client = s3_client()
        extra = {"ContentType": ctype}
        client.put_object(Bucket=_s3_bucket(), Key=object_key(name), Body=data, **extra)
        return f"/api/uploads/{name}"

    if use_gridfs():
        _gridfs_put(name, data, content_type)
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


def save_upload(name: str, upload_file, content_type: str | None = None) -> str:
    """Persist a FastAPI UploadFile; returns `/api/uploads/{name}`."""
    ctype = content_type or getattr(upload_file, "content_type", None)
    return save_fileobj(name, upload_file.file, content_type=ctype)


def delete(name: str) -> None:
    if not name:
        return
    if use_object_storage():
        from .paths import _s3_bucket

        try:
            s3_client().delete_object(Bucket=_s3_bucket(), Key=object_key(name))
        except Exception as exc:
            logger.warning("S3 delete failed for %s: %s", name, exc)
        return
    if use_gridfs():
        _gridfs_delete(name)
        # best-effort local cleanup if a leftover exists
        path = UPLOAD_DIR / name
        path.unlink(missing_ok=True)
        return
    path = UPLOAD_DIR / name
    path.unlink(missing_ok=True)


def exists(name: str) -> bool:
    if not name:
        return False
    if use_object_storage():
        from .paths import _s3_bucket

        try:
            s3_client().head_object(Bucket=_s3_bucket(), Key=object_key(name))
            return True
        except Exception:
            return False
    if use_gridfs():
        if _gridfs_exists(name):
            return True
        # fallback: file still on ephemeral disk from before migration
        return (UPLOAD_DIR / name).is_file()
    return (UPLOAD_DIR / name).is_file()


def read_bytes(name: str) -> bytes | None:
    if not name:
        return None
    if use_object_storage():
        from .paths import _s3_bucket

        try:
            obj = s3_client().get_object(Bucket=_s3_bucket(), Key=object_key(name))
            return obj["Body"].read()
        except Exception as exc:
            logger.debug("S3 get failed for %s: %s", name, exc)
            return None
    if use_gridfs():
        data = _gridfs_get(name)
        if data is not None:
            return data
        path = UPLOAD_DIR / name
        if path.is_file():
            return path.read_bytes()
        return None
    path = UPLOAD_DIR / name
    if path.is_file():
        return path.read_bytes()
    return None


def size_bytes(name: str) -> int | None:
    if not name:
        return None
    if use_object_storage():
        from .paths import _s3_bucket

        try:
            meta = s3_client().head_object(Bucket=_s3_bucket(), Key=object_key(name))
            return int(meta.get("ContentLength") or 0) or None
        except Exception:
            return None
    if use_gridfs():
        size = _gridfs_size(name)
        if size is not None:
            return size
        path = UPLOAD_DIR / name
        if path.is_file():
            return path.stat().st_size
        return None
    path = UPLOAD_DIR / name
    if path.is_file():
        return path.stat().st_size
    return None


def local_path(name: str) -> Path | None:
    """Filesystem path when using local storage; None for object/GridFS storage."""
    if use_object_storage() or use_gridfs() or not name:
        return None
    path = UPLOAD_DIR / name
    return path if path.is_file() else None


def public_cdn_url(name: str) -> str | None:
    """Absolute CDN URL when S3_PUBLIC_BASE_URL is configured."""
    base = (os.environ.get("S3_PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if not name or not base:
        return None
    key = object_key(name)
    return f"{base}/{key}"


def uses_streamed_uploads() -> bool:
    """True when /api/uploads must be served by an app route (not StaticFiles)."""
    return use_object_storage() or use_gridfs()
