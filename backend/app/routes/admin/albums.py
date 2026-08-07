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

# ---- Albums ----
@router.get("/albums")
async def admin_list_albums(admin=Depends(require_admin)):
    db = get_db()
    return await db.albums.find({}, {"_id": 0}).sort("sortOrder", 1).to_list(200)


@router.post("/albums")
async def admin_create_album(payload: Album, admin=Depends(require_admin)):
    db = get_db()
    if not payload.slug:
        payload.slug = slugify(payload.title)
    doc = payload.model_dump()
    await db.albums.insert_one(doc.copy())
    return doc


@router.put("/albums/{album_id}")
async def admin_update_album(album_id: str, payload: Album, admin=Depends(require_admin)):
    db = get_db()
    payload.id = album_id
    doc = payload.model_dump()
    await db.albums.update_one({"id": album_id}, {"$set": doc})
    return doc


@router.delete("/albums/{album_id}")
async def admin_delete_album(album_id: str, admin=Depends(require_admin)):
    db = get_db()
    await db.albums.delete_one({"id": album_id})
    return {"ok": True}


