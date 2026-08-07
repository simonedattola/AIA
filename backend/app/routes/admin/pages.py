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

# ---- Pages ----
@router.get("/pages")
async def admin_list_pages(admin=Depends(require_admin)):
    db = get_db()
    pages = await db.pages.find({}, {"_id": 0}).to_list(200)
    pages.sort(key=lambda p: (0 if p.get("template") == "system" else 1, p.get("menuOrder", 100), p.get("title", "")))
    return pages


@router.post("/pages/reconcile-system")
async def admin_reconcile_system_pages(admin=Depends(require_admin)):
    """Crea/aggiorna le pagine di sistema mancanti o incomplete."""
    from ...seed import ensure_all_system_pages

    result = await ensure_all_system_pages()
    db = get_db()
    pages = await db.pages.find({}, {"_id": 0}).to_list(200)
    pages.sort(key=lambda p: (0 if p.get("template") == "system" else 1, p.get("menuOrder", 100), p.get("title", "")))
    return {"ok": True, **result, "pages": pages}


@router.post("/pages/{page_id}/reset-blocks")
async def admin_reset_page_blocks(page_id: str, admin=Depends(require_admin)):
    """Ripristina i blocchi predefiniti per la pagina (utile se il contenuto è stato svuotato)."""
    from ...seed import suggested_page_content

    db = get_db()
    page = await db.pages.find_one({"id": page_id}, {"_id": 0})
    if not page:
        raise HTTPException(404, "Pagina non trovata")
    suggested = suggested_page_content(page.get("slug") or "", page)
    blocks = suggested.get("blocks") or []
    if not blocks:
        raise HTTPException(400, "Nessun contenuto predefinito per questa pagina")
    patch = {**suggested, "updatedAt": datetime.now(timezone.utc).isoformat()}
    await db.pages.update_one({"id": page_id}, {"$set": patch})
    updated = await db.pages.find_one({"id": page_id}, {"_id": 0})
    return updated


@router.get("/pages/{page_id}")
async def admin_get_page(page_id: str, admin=Depends(require_admin)):
    db = get_db()
    p = await db.pages.find_one({"id": page_id}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Pagina non trovata")
    return p


@router.put("/pages/{page_id}")
async def admin_update_page(page_id: str, payload: Page, admin=Depends(require_admin)):
    db = get_db()
    payload.id = page_id
    payload.bodyHtml = sanitize_html(payload.bodyHtml)
    from ...blocks_sanitize import sanitize_blocks
    payload.blocks = sanitize_blocks(payload.blocks)
    payload.updatedAt = datetime.now(timezone.utc).isoformat()
    doc = payload.model_dump()
    await db.pages.update_one({"id": page_id}, {"$set": doc}, upsert=True)
    return doc


@router.post("/pages")
async def admin_create_page(payload: Page, admin=Depends(require_admin)):
    db = get_db()
    if not payload.slug:
        payload.slug = slugify(payload.title)
    # ensure unique slug
    base = payload.slug
    i = 1
    while await db.pages.find_one({"slug": payload.slug}, {"_id": 0, "id": 1}):
        i += 1
        payload.slug = f"{base}-{i}"
    payload.bodyHtml = sanitize_html(payload.bodyHtml)
    from ...blocks_sanitize import sanitize_blocks
    payload.blocks = sanitize_blocks(payload.blocks)
    doc = payload.model_dump()
    await db.pages.insert_one(doc.copy())
    return doc


@router.delete("/pages/{page_id}")
async def admin_delete_page(page_id: str, admin=Depends(require_admin)):
    db = get_db()
    page = await db.pages.find_one({"id": page_id}, {"_id": 0})
    if not page:
        raise HTTPException(404, "Pagina non trovata")
    if page.get("template") == "system":
        raise HTTPException(400, "Le pagine di sistema non possono essere eliminate")
    await db.pages.delete_one({"id": page_id})
    return {"ok": True}


