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

# ---- Articles ----
@router.get("/article-categories")
async def admin_list_article_categories(admin=Depends(require_admin)):
    from ...article_categories import get_admin_article_categories

    db = get_db()
    return await get_admin_article_categories(db)


@router.post("/article-categories")
async def admin_add_article_category(payload: ArticleCategoryCreate, admin=Depends(require_admin)):
    from ...article_categories import add_article_category, normalize_category

    name = normalize_category(payload.name)
    if not name:
        raise HTTPException(400, "Nome categoria obbligatorio")
    db = get_db()
    try:
        return await add_article_category(db, name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/articles")
async def admin_list_articles(admin=Depends(require_admin)):
    db = get_db()
    return await db.articles.find({}, {"_id": 0}).sort("publishedAt", -1).to_list(500)


@router.get("/articles/{article_id}")
async def admin_get_article(article_id: str, admin=Depends(require_admin)):
    from ...article_body import normalize_article_body_html
    from ...media_urls import resolve_media_fields

    db = get_db()
    a = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not a:
        raise HTTPException(404, "Articolo non trovato")
    a["bodyHtml"] = normalize_article_body_html(a.get("bodyHtml") or "")
    resolve_media_fields(a)
    return a


@router.post("/articles")
async def admin_create_article(payload: ArticleCreate, admin=Depends(require_admin)):
    from ...article_categories import ensure_category_exists

    db = get_db()
    category = await ensure_category_exists(db, payload.category)
    slug = (payload.slug or slugify(payload.title)).strip()
    # ensure unique slug
    base = slug
    i = 1
    while await db.articles.find_one({"slug": slug}, {"_id": 0, "id": 1}):
        i += 1
        slug = f"{base}-{i}"
    art = Article(
        slug=slug,
        title=payload.title,
        category=category or payload.category,
        excerpt=payload.excerpt,
        bodyHtml=sanitize_html(payload.bodyHtml),
        coverUrl=payload.coverUrl,
        coverInGallery=payload.coverInGallery,
        bodyInGallery=payload.bodyInGallery,
        authorName=payload.authorName,
        relatedMemberIds=payload.relatedMemberIds or [],
        tags=payload.tags or [],
        portalOnly=payload.portalOnly,
        status=payload.status,
        publishedAt=payload.publishedAt or datetime.now(timezone.utc).isoformat(),
    )
    doc = art.model_dump()
    await db.articles.insert_one(doc.copy())
    from ...gallery import sync_article_gallery

    await sync_article_gallery(db, doc)
    return doc


@router.put("/articles/{article_id}")
async def admin_update_article(article_id: str, payload: Article, admin=Depends(require_admin)):
    from ...article_categories import ensure_category_exists
    from ...article_sanitize import sanitize_article_html

    db = get_db()
    existing = await db.articles.find_one({"id": article_id}, {"_id": 0, "id": 1, "legacyWpId": 1})
    if not existing:
        raise HTTPException(404, "Articolo non trovato")
    payload.id = article_id
    payload.category = await ensure_category_exists(db, payload.category) or payload.category
    legacy = bool(payload.legacyWpId or existing.get("legacyWpId"))
    payload.bodyHtml = sanitize_article_html(payload.bodyHtml, legacy=legacy)
    payload.updatedAt = datetime.now(timezone.utc).isoformat()
    doc = payload.model_dump()
    await db.articles.update_one({"id": article_id}, {"$set": doc})
    from ...gallery import sync_article_gallery

    await sync_article_gallery(db, doc)
    return doc


@router.delete("/articles/{article_id}")
async def admin_delete_article(article_id: str, admin=Depends(require_admin)):
    db = get_db()
    await db.articles.delete_one({"id": article_id})
    from ...gallery import ARTICLE_GALLERY_SOURCES

    await db.gallery_images.delete_many(
        {"articleId": article_id, "source": {"$in": list(ARTICLE_GALLERY_SOURCES)}}
    )
    return {"ok": True}


@router.post("/articles/import-legacy")
async def admin_import_legacy_articles(admin=Depends(require_admin)):
    """Importa/aggiorna articoli da www.aia-legnano.it (WordPress)."""
    from ...legacy_article_import import run_legacy_article_import

    db = get_db()
    return await run_legacy_article_import(db, dry_run=False, download_images=True)


@router.post("/articles/cleanup-legacy")
async def admin_cleanup_legacy_articles(admin=Depends(require_admin)):
    """Rimuove articoli spazzatura e ricalcola tag associati (nome+cognome)."""
    from ...article_cleanup import run_article_cleanup

    db = get_db()
    return await run_article_cleanup(db)


