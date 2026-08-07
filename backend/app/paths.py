"""Shared filesystem paths and object-storage configuration for uploads."""
from __future__ import annotations

import os
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", str(BACKEND_ROOT / "uploads")))

# STORAGE_BACKEND=local (default) | s3
# When s3: works with AWS S3 or S3-compatible APIs (Cloudflare R2, MinIO).
STORAGE_BACKEND = (os.environ.get("STORAGE_BACKEND") or "local").strip().lower()
S3_BUCKET = (os.environ.get("S3_BUCKET") or "").strip()
S3_ENDPOINT_URL = (os.environ.get("S3_ENDPOINT_URL") or "").strip() or None
S3_REGION = (os.environ.get("S3_REGION") or "auto").strip()
S3_ACCESS_KEY_ID = (os.environ.get("S3_ACCESS_KEY_ID") or os.environ.get("AWS_ACCESS_KEY_ID") or "").strip()
S3_SECRET_ACCESS_KEY = (
    os.environ.get("S3_SECRET_ACCESS_KEY") or os.environ.get("AWS_SECRET_ACCESS_KEY") or ""
).strip()
S3_PREFIX = (os.environ.get("S3_PREFIX") or "").strip().strip("/")
# Public CDN / bucket URL (CloudFront, R2 custom domain, public S3 website).
# When set, /api/uploads/{name} resolves to {S3_PUBLIC_BASE_URL}/{prefix?}{name}.
S3_PUBLIC_BASE_URL = (os.environ.get("S3_PUBLIC_BASE_URL") or "").strip().rstrip("/")


def use_object_storage() -> bool:
    return STORAGE_BACKEND in {"s3", "r2", "minio"} and bool(S3_BUCKET)


def object_key(name: str) -> str:
    """Object key inside the bucket for a stored basename."""
    base = name.lstrip("/")
    if S3_PREFIX:
        return f"{S3_PREFIX}/{base}"
    return base


def s3_client():
    """Return a boto3 S3 client configured for AWS or R2/MinIO."""
    if not use_object_storage():
        raise RuntimeError("Object storage is not configured (set STORAGE_BACKEND=s3 and S3_BUCKET)")
    import boto3
    from botocore.config import Config

    kwargs: dict = {
        "service_name": "s3",
        "region_name": S3_REGION or "auto",
        "config": Config(signature_version="s3v4"),
    }
    if S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = S3_ENDPOINT_URL
    if S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = S3_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = S3_SECRET_ACCESS_KEY
    return boto3.client(**kwargs)
