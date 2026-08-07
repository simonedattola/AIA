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

# ---- Utility (area associati) ----
_UTILITY_SECTIONS = {"link_utili"}


@router.get("/utility")
async def admin_get_utility(admin=Depends(require_admin)):
    from ...designation_filters import event_date_in_season_clause, merge_mongo_queries

    db = get_db()
    settings = await db.site_settings.find_one({"id": "site-settings"}, {"_id": 0, "utilityPolo": 1})
    items = await db.utility_items.find({}, {"_id": 0}).sort("sortOrder", 1).to_list(500)
    polo = (settings or {}).get("utilityPolo") or {"bodyHtml": ""}
    polo = {"bodyHtml": polo.get("bodyHtml") or ""}
    material_count = await db.events.count_documents(
        merge_mongo_queries(
            {"utilityMaterial.0": {"$exists": True}},
            event_date_in_season_clause(),
        )
    )
    return {"polo": polo, "items": items, "eventMaterialCount": material_count}


@router.put("/utility/polo")
async def admin_update_utility_polo(payload: UtilityPolo, admin=Depends(require_admin)):
    db = get_db()
    polo = payload.model_dump()
    polo["bodyHtml"] = sanitize_html(polo.get("bodyHtml") or "")
    await db.site_settings.update_one(
        {"id": "site-settings"},
        {"$set": {"utilityPolo": polo}},
        upsert=True,
    )
    return polo


@router.post("/utility-items")
async def admin_create_utility_item(payload: UtilityItem, admin=Depends(require_admin)):
    section = (payload.section or "").strip()
    if section not in _UTILITY_SECTIONS:
        raise HTTPException(400, "Sezione non valida")
    if not (payload.title or "").strip():
        raise HTTPException(400, "Titolo obbligatorio")
    db = get_db()
    doc = payload.model_dump()
    doc["section"] = section
    doc["title"] = payload.title.strip()
    if not (doc.get("url") or doc.get("fileUrl")):
        raise HTTPException(400, "URL o file obbligatorio")
    await db.utility_items.insert_one(doc.copy())
    return doc


@router.put("/utility-items/{item_id}")
async def admin_update_utility_item(item_id: str, payload: UtilityItem, admin=Depends(require_admin)):
    section = (payload.section or "").strip()
    if section not in _UTILITY_SECTIONS:
        raise HTTPException(400, "Sezione non valida")
    if not (payload.title or "").strip():
        raise HTTPException(400, "Titolo obbligatorio")
    db = get_db()
    payload.id = item_id
    doc = payload.model_dump()
    doc["section"] = section
    doc["title"] = payload.title.strip()
    if not (doc.get("url") or doc.get("fileUrl")):
        raise HTTPException(400, "URL o file obbligatorio")
    await db.utility_items.update_one({"id": item_id}, {"$set": doc})
    return doc


@router.delete("/utility-items/{item_id}")
async def admin_delete_utility_item(item_id: str, admin=Depends(require_admin)):
    db = get_db()
    await db.utility_items.delete_one({"id": item_id})
    return {"ok": True}


@router.get("/utility/event/{event_id}")
@router.get("/utility/rto/{event_id}")
async def admin_get_utility_event_material(event_id: str, admin=Depends(require_admin)):
    from ...media_urls import resolve_attachments

    db = get_db()
    ev = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not ev:
        raise HTTPException(status_code=404, detail="Evento non trovato")
    return {
        "id": ev["id"],
        "date": ev.get("date", ""),
        "orario": ev.get("orario", ""),
        "tipo": ev.get("tipo", ""),
        "titolo": ev.get("titolo", ""),
        "descrizione": ev.get("descrizione", ""),
        "utilityMaterial": resolve_attachments(ev.get("utilityMaterial")),
    }


@router.put("/utility/event/{event_id}/material")
@router.put("/utility/rto/{event_id}/material")
async def admin_update_utility_event_material(
    event_id: str, payload: EventUtilityMaterialUpdate, admin=Depends(require_admin)
):
    from ...media_urls import resolve_attachments

    db = get_db()
    ev = await db.events.find_one({"id": event_id}, {"_id": 0, "id": 1})
    if not ev:
        raise HTTPException(status_code=404, detail="Evento non trovato")
    material = [a.model_dump() for a in (payload.utilityMaterial or [])]
    await db.events.update_one({"id": event_id}, {"$set": {"utilityMaterial": material}})
    return {"ok": True, "utilityMaterial": resolve_attachments(material)}


