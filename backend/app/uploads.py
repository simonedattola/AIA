"""Safe upload helpers: extension allowlist + size limits."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from .paths import UPLOAD_DIR

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
# SVG excluded: served as static files → stored XSS risk
ATTACHMENT_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
    ".zip",
    ".mp4",
    ".webm",
    ".mov",
}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}

DEFAULT_IMAGE_MAX_BYTES = 8 * 1024 * 1024
DEFAULT_ATTACHMENT_MAX_BYTES = 10 * 1024 * 1024
DEFAULT_VIDEO_MAX_BYTES = 50 * 1024 * 1024
DEFAULT_MESSAGE_ATTACHMENT_MAX_BYTES = 10 * 1024 * 1024


def _extension(filename: str | None) -> str:
    return Path(filename or "").suffix.lower() or ".bin"


async def save_upload(
    file: UploadFile,
    *,
    allowed_ext: set[str],
    max_bytes: int,
    name_prefix: str = "",
) -> tuple[Path, str, int]:
    """
    Stream upload to disk with a hard size limit.
    Returns (absolute_path, stored_filename, size_bytes).
    """
    ext = _extension(file.filename)
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail="Formato file non supportato")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{name_prefix}{uuid.uuid4().hex}{ext}"
    target = UPLOAD_DIR / name

    size = 0
    chunk_size = 64 * 1024
    try:
        with target.open("wb") as out:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    out.close()
                    target.unlink(missing_ok=True)
                    limit_mb = max(1, max_bytes // (1024 * 1024))
                    raise HTTPException(
                        status_code=400,
                        detail=f"File troppo grande (max {limit_mb} MB)",
                    )
                out.write(chunk)
    except HTTPException:
        raise
    except Exception:
        target.unlink(missing_ok=True)
        raise

    return target, name, size


def max_bytes_for_attachment(ext: str) -> int:
    if ext in VIDEO_EXTENSIONS:
        return DEFAULT_VIDEO_MAX_BYTES
    return DEFAULT_ATTACHMENT_MAX_BYTES
