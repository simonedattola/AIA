"""Shared filesystem paths and object-storage configuration for uploads."""
from __future__ import annotations

import os
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
_upload_env = (os.environ.get("UPLOAD_DIR") or "").strip()
UPLOAD_DIR = Path(_upload_env) if _upload_env else (BACKEND_ROOT / "uploads")

# STORAGE_BACKEND:
#   auto   (default) → GridFS su MongoDB Atlas (mongodb+srv), altrimenti disco locale
#   local  → solo disco (UPLOAD_DIR)
#   gridfs → MongoDB GridFS (persiste su Atlas, gratis, ok su Railway)
#   s3/r2/minio → object storage
def storage_backend() -> str:
    return (os.environ.get("STORAGE_BACKEND") or "auto").strip().lower()


# Back-compat for imports/tests that read the module constant
STORAGE_BACKEND = storage_backend()


def _s3_bucket() -> str:
    return (os.environ.get("S3_BUCKET") or "").strip()


S3_BUCKET = _s3_bucket()
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
    backend = storage_backend()
    return backend in {"s3", "r2", "minio"} and bool(_s3_bucket())


def use_gridfs() -> bool:
    """Persist uploads in MongoDB (Atlas free tier) — survives Railway redeploys."""
    if use_object_storage():
        return False
    backend = storage_backend()
    if backend in {"gridfs", "mongo", "mongodb"}:
        return True
    if backend == "local":
        return False
    # auto (default): Atlas / remote SRV → GridFS; docker/local mongo → disk + volume
    if backend in {"", "auto"}:
        mongo = (os.environ.get("MONGO_URL") or "").lower()
        return "mongodb+srv://" in mongo
    return False


def object_key(name: str) -> str:
    """Object key inside the bucket for a stored basename."""
    base = name.lstrip("/")
    prefix = (os.environ.get("S3_PREFIX") or "").strip().strip("/")
    if prefix:
        return f"{prefix}/{base}"
    return base


def s3_client():
    """Return a boto3 S3 client configured for AWS or R2/MinIO."""
    if not use_object_storage():
        raise RuntimeError("Object storage is not configured (set STORAGE_BACKEND=s3 and S3_BUCKET)")
    import boto3
    from botocore.config import Config

    endpoint = (os.environ.get("S3_ENDPOINT_URL") or "").strip() or None
    region = (os.environ.get("S3_REGION") or "auto").strip()
    key = (os.environ.get("S3_ACCESS_KEY_ID") or os.environ.get("AWS_ACCESS_KEY_ID") or "").strip()
    secret = (
        os.environ.get("S3_SECRET_ACCESS_KEY") or os.environ.get("AWS_SECRET_ACCESS_KEY") or ""
    ).strip()
    kwargs: dict = {
        "service_name": "s3",
        "region_name": region or "auto",
        "config": Config(signature_version="s3v4"),
    }
    if endpoint:
        kwargs["endpoint_url"] = endpoint
    if key and secret:
        kwargs["aws_access_key_id"] = key
        kwargs["aws_secret_access_key"] = secret
    return boto3.client(**kwargs)
