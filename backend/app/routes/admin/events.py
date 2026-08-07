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

# ---- Events ----
@router.get("/event-types")
async def admin_list_event_types(admin=Depends(require_admin)):
    from ...event_categories import get_admin_event_types

    db = get_db()
    return await get_admin_event_types(db)


@router.post("/event-types")
async def admin_add_event_type(payload: ArticleCategoryCreate, admin=Depends(require_admin)):
    from ...event_categories import add_event_type, normalize_event_type

    name = normalize_event_type(payload.name)
    if not name:
        raise HTTPException(400, "Nome tipo obbligatorio")
    db = get_db()
    try:
        return await add_event_type(db, name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/events")
async def admin_list_events(admin=Depends(require_admin)):
    from ...designation_filters import event_date_in_season_clause

    db = get_db()
    q = event_date_in_season_clause() or {}
    return await db.events.find(q, {"_id": 0}).sort("date", -1).to_list(500)


@router.post("/events")
async def admin_create_event(payload: Event, admin=Depends(require_admin)):
    db = get_db()
    from ...event_reminders import normalize_event_time
    from ...event_categories import ensure_event_type_exists

    doc = payload.model_dump()
    doc["orario"] = normalize_event_time(doc.get("orario"))
    doc["tipo"] = await ensure_event_type_exists(db, doc.get("tipo") or "Riunione")
    await db.events.insert_one(doc.copy())
    from ...event_reminders import schedule_event_created_notifications

    schedule_event_created_notifications(db, doc)
    return doc


@router.put("/events/{event_id}")
async def admin_update_event(event_id: str, payload: Event, admin=Depends(require_admin)):
    db = get_db()
    from ...event_reminders import normalize_event_time
    from ...event_categories import ensure_event_type_exists

    existing = await db.events.find_one(
        {"id": event_id},
        {"_id": 0, "id": 1, "utilityMaterial": 1},
    )
    if existing is None:
        raise HTTPException(status_code=404, detail="Evento non trovato")
    payload.id = event_id
    doc = payload.model_dump()
    doc["orario"] = normalize_event_time(doc.get("orario"))
    doc["tipo"] = await ensure_event_type_exists(db, doc.get("tipo") or "Riunione")
    doc["utilityMaterial"] = existing.get("utilityMaterial") or []
    await db.events.update_one({"id": event_id}, {"$set": doc})
    return doc


@router.delete("/events/{event_id}")
async def admin_delete_event(event_id: str, admin=Depends(require_admin)):
    db = get_db()
    await db.events.delete_one({"id": event_id})
    return {"ok": True}


