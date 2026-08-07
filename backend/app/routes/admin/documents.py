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

# ---- Documents (downloads) ----
@router.get("/documents")
async def admin_list_documents(admin=Depends(require_admin)):
    from ...media_urls import file_size_label_for_media_url

    db = get_db()
    docs = await db.documents.find({}, {"_id": 0}).sort("sortOrder", 1).to_list(500)
    for d in docs:
        if not (d.get("fileSize") or "").strip() and d.get("fileUrl"):
            label = file_size_label_for_media_url(d["fileUrl"])
            if label:
                d["fileSize"] = label
    return docs


async def _enrich_document(doc: dict) -> dict:
    from ...document_sections import ensure_section_exists, normalize_document_category
    from ...media_urls import file_size_label_for_media_url

    db = get_db()
    section = await normalize_document_category(db, doc.get("category"), doc.get("section"))
    doc["category"] = section
    doc["section"] = section
    await ensure_section_exists(db, section)
    if not (doc.get("fileSize") or "").strip() and doc.get("fileUrl"):
        label = file_size_label_for_media_url(doc["fileUrl"])
        if label:
            doc["fileSize"] = label
    return doc


@router.get("/document-sections")
async def admin_list_document_sections(admin=Depends(require_admin)):
    from ...document_sections import get_admin_document_sections

    db = get_db()
    return await get_admin_document_sections(db)


@router.post("/document-sections")
async def admin_add_document_section(payload: ArticleCategoryCreate, admin=Depends(require_admin)):
    from ...document_sections import add_document_section, normalize_section_name

    name = normalize_section_name(payload.name)
    if not name:
        raise HTTPException(400, "Nome sezione obbligatorio")
    db = get_db()
    try:
        return await add_document_section(db, name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/documents")
async def admin_create_document(payload: Document, admin=Depends(require_admin)):
    db = get_db()
    doc = await _enrich_document(payload.model_dump())
    await db.documents.insert_one(doc.copy())
    return doc


@router.put("/documents/{doc_id}")
async def admin_update_document(doc_id: str, payload: Document, admin=Depends(require_admin)):
    db = get_db()
    payload.id = doc_id
    doc = await _enrich_document(payload.model_dump())
    await db.documents.update_one({"id": doc_id}, {"$set": doc})
    return doc


@router.delete("/documents/{doc_id}")
async def admin_delete_document(doc_id: str, admin=Depends(require_admin)):
    db = get_db()
    await db.documents.delete_one({"id": doc_id})
    return {"ok": True}



@router.post("/documents/import-aia-figc")
async def admin_import_aia_documents(admin=Depends(require_admin)):
    """Importa o aggiorna i documenti da https://www.aia-figc.it/download/"""
    from ...scrapers.aia_downloads import import_aia_downloads

    db = get_db()
    result = await import_aia_downloads(db, download_files=True, replace_existing=True)
    return {"ok": True, **result}


@router.post("/documents/import-aia-legnano")
async def admin_import_legnano_documents(admin=Depends(require_admin)):
    """Importa o aggiorna i documenti da https://www.aia-legnano.it/download/"""
    from ...scrapers.aia_legnano_downloads import import_legnano_downloads

    db = get_db()
    result = await import_legnano_downloads(db, download_files=True, replace_existing=True)
    return {"ok": True, **result}


@router.post("/documents/import-all-sources")
async def admin_import_all_documents(admin=Depends(require_admin)):
    """Importa documenti da AIA FIGC e AIA Legnano."""
    from ...scrapers.aia_downloads import import_aia_downloads
    from ...scrapers.aia_legnano_downloads import import_legnano_downloads

    db = get_db()
    figc = await import_aia_downloads(db, download_files=True, replace_existing=True)
    legnano = await import_legnano_downloads(db, download_files=True, replace_existing=True)
    return {
        "ok": True,
        "figc": figc,
        "legnano": legnano,
        "imported": (figc.get("imported") or 0) + (legnano.get("imported") or 0),
        "errors": (figc.get("errors") or 0) + (legnano.get("errors") or 0),
    }


