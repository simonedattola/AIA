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

# ---- Testimonials ----
async def _attach_testimonial_member(db, doc: dict) -> dict:
    """Imposta memberSlug quando la testimonianza è collegata a un associato."""
    mid = doc.get("memberId")
    if mid:
        m = await db.members.find_one({"id": mid}, {"_id": 0, "slug": 1})
        doc["memberSlug"] = (m or {}).get("slug") or ""
    else:
        doc["memberSlug"] = ""
    return doc


@router.get("/testimonials")
async def admin_list_testimonials(admin=Depends(require_admin)):
    db = get_db()
    return await db.testimonials.find({}, {"_id": 0}).sort("sortOrder", 1).to_list(100)


@router.post("/testimonials")
async def admin_create_testimonial(payload: Testimonial, admin=Depends(require_admin)):
    db = get_db()
    doc = await _attach_testimonial_member(db, payload.model_dump())
    await db.testimonials.insert_one(doc.copy())
    return doc


@router.put("/testimonials/{t_id}")
async def admin_update_testimonial(t_id: str, payload: Testimonial, admin=Depends(require_admin)):
    db = get_db()
    payload.id = t_id
    doc = await _attach_testimonial_member(db, payload.model_dump())
    await db.testimonials.update_one({"id": t_id}, {"$set": doc})
    return doc


@router.delete("/testimonials/{t_id}")
async def admin_delete_testimonial(t_id: str, admin=Depends(require_admin)):
    from ...seed import _set_seed_flag

    db = get_db()
    await db.testimonials.delete_one({"id": t_id})
    if await db.testimonials.count_documents({}) == 0:
        await _set_seed_flag("testimonials")
    return {"ok": True}


