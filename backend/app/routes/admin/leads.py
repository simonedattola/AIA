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

# ---- Leads ----
LEAD_STATUSES = {"new", "contacted", "archived"}


@router.get("/leads")
async def admin_list_leads(admin=Depends(require_admin)):
    db = get_db()
    return await db.leads.find({}, {"_id": 0}).sort("createdAt", -1).to_list(1000)


@router.put("/leads/{lead_id}")
async def admin_update_lead_status(lead_id: str, payload: dict, admin=Depends(require_admin)):
    db = get_db()
    status = (payload.get("status") or "new").strip().lower()
    if status not in LEAD_STATUSES:
        raise HTTPException(400, f"Stato non valido (ammessi: {', '.join(sorted(LEAD_STATUSES))})")
    await db.leads.update_one({"id": lead_id}, {"$set": {"status": status}})
    return {"ok": True}


@router.delete("/leads/{lead_id}")
async def admin_delete_lead(lead_id: str, admin=Depends(require_admin)):
    db = get_db()
    await db.leads.delete_one({"id": lead_id})
    return {"ok": True}


