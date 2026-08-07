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

# ---- Designations ----
def _designation_list_query() -> dict:
    from ...designation_filters import (
        current_season_label,
        match_date_in_season_clause,
        merge_mongo_queries,
    )

    return merge_mongo_queries(
        {"role": {"$not": {"$regex": "osservatore", "$options": "i"}}},
        match_date_in_season_clause(current_season_label()),
    )


async def _validate_designation_payload(db, doc: dict) -> None:
    from ...member_roles import is_observer_designation_role, has_designations, normalize_member

    if is_observer_designation_role(doc.get("role")):
        raise HTTPException(status_code=400, detail="Le designazioni con ruolo Osservatore non sono gestite qui")
    mid = doc.get("memberId")
    if mid:
        m = await db.members.find_one({"id": mid}, {"_id": 0})
        if m:
            normalize_member(m)
            if not has_designations(m.get("memberRole")):
                raise HTTPException(status_code=400, detail="Il nominativo deve essere un arbitro o assistente")


@router.get("/designations")
async def admin_list_designations(admin=Depends(require_admin)):
    db = get_db()
    items = await db.designations.find(_designation_list_query(), {"_id": 0}).sort("matchDate", -1).to_list(500)
    from ...designation_enrich import build_member_lookups, enrich_designation
    from ...member_roles import legacy_arbitri_query

    members = await db.members.find(
        legacy_arbitri_query(),
        {"_id": 0, "id": 1, "slug": 1, "firstName": 1, "lastName": 1, "kind": 1, "memberRole": 1},
    ).to_list(2000)
    slug_by_id, member_by_name = build_member_lookups(members)
    for item in items:
        enrich_designation(item, slug_by_id, member_by_name)
    return items


async def _attach_member_slug(db, doc: dict) -> dict:
    """Ensure memberSlug is set when memberId is present."""
    mid = doc.get("memberId")
    if mid and not doc.get("memberSlug"):
        m = await db.members.find_one({"id": mid}, {"_id": 0, "slug": 1})
        if m:
            doc["memberSlug"] = m.get("slug", "")
    if not doc.get("matchLabel") and doc.get("matchHome") and doc.get("matchAway"):
        doc["matchLabel"] = f"{doc['matchHome']} - {doc['matchAway']}"
    return doc


@router.post("/designations")
async def admin_create_designation(payload: Designation, admin=Depends(require_admin)):
    db = get_db()
    doc = payload.model_dump()
    await _validate_designation_payload(db, doc)
    doc = await _attach_member_slug(db, doc)
    await db.designations.insert_one(doc.copy())
    return doc


@router.put("/designations/{des_id}")
async def admin_update_designation(des_id: str, payload: Designation, admin=Depends(require_admin)):
    db = get_db()
    payload.id = des_id
    doc = payload.model_dump()
    await _validate_designation_payload(db, doc)
    doc = await _attach_member_slug(db, doc)
    await db.designations.update_one({"id": des_id}, {"$set": doc})
    return doc


@router.delete("/designations/{des_id}")
async def admin_delete_designation(des_id: str, admin=Depends(require_admin)):
    db = get_db()
    await db.designations.delete_one({"id": des_id})
    return {"ok": True}


@router.post("/designations/sync-aia")
async def admin_sync_designations_aia(
    payload: DesignationSyncRequest = DesignationSyncRequest(),
    admin=Depends(require_admin),
):
    """Scrape designazioni from AIA FIGC Lombardia (Legnano section by default) and import."""
    try:
        return await sync_from_aia_lombardia(
            section_gare=payload.sectionGare,
            filter_section=payload.filterSection,
            replace_existing=payload.replaceExisting,
            max_des_pages=payload.maxDesPages,
            trigger="manual",
        )
    except Exception as e:
        logger.exception("Designations sync failed")
        raise HTTPException(500, f"Sincronizzazione fallita: {e}") from e


@router.get("/designations/import-template")
async def admin_designations_import_template(admin=Depends(require_admin)):
    """Modello CSV per import designazioni da file."""
    return Response(
        content=IMPORT_TEMPLATE_CSV,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="designazioni_modello.csv"'},
    )


@router.post("/designations/import-file")
async def admin_import_designations_file(
    file: UploadFile = File(...),
    dry_run: bool = Form(False),
    admin=Depends(require_admin),
):
    """Importa designazioni da CSV, Excel, PDF o Word (.docx)."""
    filename = file.filename or "designazioni.csv"
    lower = filename.lower()
    if not lower.endswith(SUPPORTED_EXTENSIONS):
        raise HTTPException(
            400,
            "Formato non supportato. Usa CSV, Excel (.xlsx), PDF o Word (.docx).",
        )
    content = await file.read()
    if not content:
        raise HTTPException(400, "File vuoto.")
    try:
        return await import_designations_from_file(content, filename, dry_run=dry_run)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        logger.exception("Designations file import failed")
        raise HTTPException(500, f"Import fallito: {exc}") from exc


@router.get("/designations/sync-status")
async def admin_designations_sync_status(admin=Depends(require_admin)):
    db = get_db()
    settings = await db.site_settings.find_one({"id": "site-settings"}, {"_id": 0, "lastDesignationsSync": 1})
    return settings.get("lastDesignationsSync") if settings else {}


