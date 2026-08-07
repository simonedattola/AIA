from __future__ import annotations

from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, Response
from slugify import slugify

from ...db import get_db
from ...security import require_admin, verify_password, create_token
from ...paths import UPLOAD_DIR
from ...member_roles import strip_sensitive_member_fields
from ...uploads import (
    save_upload,
    IMAGE_EXTENSIONS,
    ATTACHMENT_EXTENSIONS,
    DEFAULT_IMAGE_MAX_BYTES,
    max_bytes_for_attachment,
)
from ...rate_limit import client_ip, enforce_rate_limit
from ...models import (
    LoginRequest, TokenResponse, AdminInfo,
    SiteSettings, Page, Article, ArticleCreate, Event,
    Official, Member, MemberCreate, Designation,
    Document, Album, Testimonial, UtilityPolo, UtilityItem, EventUtilityMaterialUpdate,
    DesignationSyncRequest, ArticleCategoryCreate,
    GalleryImageCreate, GalleryImageUpdate,
)
from ...designations_sync import sync_from_aia_lombardia
from ...designations_import import import_designations_from_file, IMPORT_TEMPLATE_CSV
from ...designations_import_extract import SUPPORTED_EXTENSIONS
from ...members_import import import_members_from_file, IMPORT_TEMPLATE_CSV as MEMBERS_IMPORT_TEMPLATE_CSV
from ...sanitize import sanitize_html
from .deps import logger, now_iso

router = APIRouter()

# ---- Upload ----
@router.post("/upload")
async def admin_upload(file: UploadFile = File(...), admin=Depends(require_admin)):
    import uuid as _u

    _target, name, _size = await save_upload(
        file,
        allowed_ext=IMAGE_EXTENSIONS,
        max_bytes=DEFAULT_IMAGE_MAX_BYTES,
    )
    from ...media_urls import resolve_media_url

    rel_path = f"/api/uploads/{name}"
    abs_url = resolve_media_url(rel_path)
    db = get_db()
    doc = {
        "id": _u.uuid4().hex,
        "filename": file.filename,
        "path": rel_path,
        "url": abs_url,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    await db.media.insert_one(doc.copy())
    return doc


@router.post("/upload-attachment")
async def admin_upload_attachment(file: UploadFile = File(...), admin=Depends(require_admin)):
    import uuid as _u
    from pathlib import Path as _Path

    ext = _Path(file.filename or "").suffix.lower() or ".bin"
    max_bytes = max_bytes_for_attachment(ext)
    target, name, size = await save_upload(
        file,
        allowed_ext=ATTACHMENT_EXTENSIONS,
        max_bytes=max_bytes,
        name_prefix="att_",
    )
    from ...media_urls import resolve_media_url

    rel_path = f"/api/uploads/{name}"
    return {
        "id": _u.uuid4().hex,
        "fileName": file.filename or name,
        "fileUrl": rel_path,
        "url": resolve_media_url(rel_path),
        "fileSize": size,
        "mimeType": file.content_type or "",
    }


@router.get("/media")
async def admin_list_media(admin=Depends(require_admin)):
    db = get_db()
    return await db.media.find({}, {"_id": 0}).sort("createdAt", -1).to_list(500)


