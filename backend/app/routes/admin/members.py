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

# ---- Members ----
@router.get("/members")
async def admin_list_members(memberRole: Optional[str] = None, admin=Depends(require_admin)):
    db = get_db()
    from ...media_urls import resolve_media_fields
    from ...member_roles import normalize_member

    query = {"memberRole": memberRole} if memberRole else {}
    items = await db.members.find(
        query,
        {"_id": 0, "passwordHash": 0},
    ).sort([("lastName", 1), ("firstName", 1)]).to_list(500)
    for item in items:
        normalize_member(item)
        resolve_media_fields(item)
        strip_sensitive_member_fields(item)
    return items


@router.post("/members")
async def admin_create_member(payload: MemberCreate, admin=Depends(require_admin)):
    db = get_db()
    slug = (payload.slug or "").strip()
    if not slug:
        slug = slugify(f"{payload.firstName}-{payload.lastName}")
    # ensure unique slug
    base = slug
    i = 1
    while await db.members.find_one({"slug": slug}, {"_id": 0, "id": 1}):
        i += 1
        slug = f"{base}-{i}"
    from ...member_roles import normalize_member

    member = Member(
        slug=slug,
        firstName=payload.firstName.strip(),
        lastName=payload.lastName.strip(),
        memberRole=(payload.memberRole or "arbitro").strip().lower(),
        observerType=payload.observerType or "",
        boardTitle=payload.boardTitle or "",
        isPresident=payload.isPresident,
        category=payload.category,
        role=payload.role,
        kind=payload.kind,
        yearStart=payload.yearStart,
        meccanografico=payload.meccanografico,
        photoUrl=payload.photoUrl,
        bio=(payload.bio or "").strip(),
        chiSiamoText=(payload.chiSiamoText or "").strip(),
        presidentLongBio=(payload.presidentLongBio or "").strip(),
        bioHtml="",
        email=payload.email,
        phone=payload.phone,
        notes=payload.notes,
        awards=payload.awards or [],
    )
    doc = member.model_dump()
    doc.pop("passwordHash", None)
    normalize_member(doc)
    await db.members.insert_one(doc.copy())
    from ...portal_credentials import ensure_member_portal_credentials

    await ensure_member_portal_credentials(doc)
    strip_sensitive_member_fields(doc)
    return doc


@router.put("/members/{member_id}")
async def admin_update_member(member_id: str, payload: Member, admin=Depends(require_admin)):
    db = get_db()
    payload.id = member_id
    payload.updatedAt = datetime.now(timezone.utc).isoformat()
    from ...member_roles import normalize_member

    payload.bio = (payload.bio or "").strip()
    payload.chiSiamoText = (payload.chiSiamoText or "").strip()
    payload.presidentLongBio = (payload.presidentLongBio or "").strip()
    payload.bioHtml = ""
    if payload.memberRole:
        payload.memberRole = payload.memberRole.strip().lower()
    if not (payload.slug or "").strip():
        payload.slug = slugify(f"{payload.firstName}-{payload.lastName}")
    doc = payload.model_dump()
    # Mai sovrascrivere l'hash password dal payload admin (evita reset involontario)
    doc.pop("passwordHash", None)
    normalize_member(doc)
    await db.members.update_one({"id": member_id}, {"$set": doc})
    from ...media_urls import resolve_media_fields
    from ...member_category import refresh_member_category

    existing = await db.members.find_one({"id": member_id}, {"_id": 0, "passwordHash": 1, "meccanografico": 1})
    if existing:
        doc["passwordHash"] = existing.get("passwordHash") or ""
        if not doc.get("meccanografico"):
            doc["meccanografico"] = existing.get("meccanografico") or ""
    if doc.get("memberRole") == "arbitro":
        await refresh_member_category(db, doc, persist=True)
    resolve_media_fields(doc)
    from ...portal_credentials import ensure_member_portal_credentials

    await ensure_member_portal_credentials(doc)
    strip_sensitive_member_fields(doc)
    return doc


@router.delete("/members/{member_id}")
async def admin_delete_member(member_id: str, admin=Depends(require_admin)):
    db = get_db()
    await db.members.delete_one({"id": member_id})
    return {"ok": True}


@router.get("/members/import-template")
async def admin_members_import_template(admin=Depends(require_admin)):
    return Response(
        content=MEMBERS_IMPORT_TEMPLATE_CSV,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="anagrafica_modello.csv"'},
    )


@router.post("/members/import-file")
async def admin_import_members_file(
    file: UploadFile = File(...),
    dry_run: bool = Form(False),
    admin=Depends(require_admin),
):
    """Importa anagrafica da CSV, Excel, PDF o Word (.docx)."""
    filename = file.filename or "anagrafica.csv"
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
        return await import_members_from_file(content, filename, dry_run=dry_run)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        logger.exception("Members file import failed")
        raise HTTPException(500, f"Import fallito: {exc}") from exc


