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

# ---- Galleria (immagini sito) ----
@router.get("/gallery")
async def admin_list_gallery(
    status: Optional[str] = None,
    category: Optional[str] = None,
    dateFrom: Optional[str] = None,
    dateTo: Optional[str] = None,
    admin=Depends(require_admin),
):
    db = get_db()
    q: dict = {}
    if status:
        q["status"] = status
    if category:
        q["category"] = category
    if dateFrom:
        q.setdefault("photoDate", {})["$gte"] = dateFrom
    if dateTo:
        q.setdefault("photoDate", {})["$lte"] = dateTo
    return await db.gallery_images.find(q, {"_id": 0}).sort([("photoDate", -1), ("createdAt", -1)]).to_list(500)


@router.post("/gallery")
async def admin_create_gallery_image(payload: GalleryImageCreate, admin=Depends(require_admin)):
    from ...article_categories import ensure_category_exists
    from ...gallery import save_uploaded_gallery_image

    db = get_db()
    category = await ensure_category_exists(db, payload.category) if payload.category else ""
    return await save_uploaded_gallery_image(
        db,
        url=payload.url,
        path=payload.path or payload.url,
        caption=payload.caption,
        sort_order=payload.sortOrder,
        status="approved",
        source="admin",
        category=category,
        photo_date=payload.photoDate,
        source_url=payload.sourceUrl or payload.url,
        aspect=payload.aspect,
        member_ids=payload.memberIds,
    )


@router.get("/gallery/{image_id}/source")
async def admin_gallery_source_image(image_id: str, admin=Depends(require_admin)):
    """Proxy dell'immagine originale per il ritaglio in admin (evita CORS)."""
    import httpx
    from ...media_urls import public_api_base, resolve_media_url

    db = get_db()
    doc = await db.gallery_images.find_one({"id": image_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Immagine non trovata")
    src = (doc.get("sourceUrl") or doc.get("url") or doc.get("path") or "").strip()
    if not src:
        raise HTTPException(404, "Sorgente non disponibile")

    def _local_upload_response(path_value: str) -> FileResponse | None:
        name = path_value.rstrip("/").split("/")[-1]
        if not name or "/" in name or "\\" in name or name in (".", ".."):
            return None
        local = (UPLOAD_DIR / name).resolve()
        try:
            local.relative_to(UPLOAD_DIR.resolve())
        except ValueError:
            return None
        if local.is_file():
            return FileResponse(local)
        return None

    for candidate in (src, doc.get("url") or "", doc.get("path") or ""):
        c = (candidate or "").strip()
        if c.startswith("/api/uploads/"):
            found = _local_upload_response(c)
            if found:
                return found
        if "/api/uploads/" in c:
            found = _local_upload_response(c.split("/api/uploads/")[-1])
            if found:
                return found

    resolved = resolve_media_url(src)
    base = public_api_base()

    if base and resolved.startswith(base):
        rel = resolved[len(base) :]
        if rel.startswith("/api/uploads/"):
            found = _local_upload_response(rel)
            if found:
                return found

    if resolved.startswith("http://") or resolved.startswith("https://"):
        from ...url_safety import is_safe_outbound_url

        if not is_safe_outbound_url(resolved):
            raise HTTPException(400, "URL immagine non consentito")
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            try:
                r = await client.get(resolved)
                r.raise_for_status()
            except httpx.HTTPError as exc:
                raise HTTPException(502, f"Impossibile scaricare l'immagine: {exc}") from exc
            ctype = r.headers.get("content-type", "image/jpeg")
            if not str(ctype).startswith("image/"):
                raise HTTPException(400, "La risorsa remota non è un'immagine")
            if len(r.content) > 8 * 1024 * 1024:
                raise HTTPException(400, "Immagine remota troppo grande")
            return Response(content=r.content, media_type=ctype)

    raise HTTPException(404, "File non trovato")


@router.put("/gallery/{image_id}")
async def admin_update_gallery_image(
    image_id: str, payload: GalleryImageUpdate, admin=Depends(require_admin)
):
    db = get_db()
    existing = await db.gallery_images.find_one({"id": image_id}, {"_id": 0, "id": 1})
    if not existing:
        raise HTTPException(404, "Immagine non trovata")
    upd = {
        "caption": payload.caption,
        "sortOrder": payload.sortOrder,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    if payload.status:
        upd["status"] = payload.status
    if payload.category is not None:
        from ...article_categories import ensure_category_exists

        upd["category"] = await ensure_category_exists(db, payload.category) if payload.category else ""
    if payload.url is not None:
        upd["url"] = payload.url
    if payload.path is not None:
        upd["path"] = payload.path
    if payload.sourceUrl is not None:
        upd["sourceUrl"] = payload.sourceUrl
    if payload.aspect is not None:
        from ...gallery import _normalize_aspect

        upd["aspect"] = _normalize_aspect(payload.aspect)
    if payload.memberIds is not None:
        upd["memberIds"] = list(payload.memberIds)
    if payload.url is not None or payload.path is not None or payload.aspect is not None:
        upd["cropEdited"] = True
    await db.gallery_images.update_one({"id": image_id}, {"$set": upd})
    return await db.gallery_images.find_one({"id": image_id}, {"_id": 0})


@router.post("/gallery/{image_id}/approve")
async def admin_approve_gallery_image(image_id: str, admin=Depends(require_admin)):
    db = get_db()
    res = await db.gallery_images.update_one(
        {"id": image_id},
        {"$set": {"status": "approved", "updatedAt": datetime.now(timezone.utc).isoformat()}},
    )
    if not res.matched_count:
        raise HTTPException(404, "Immagine non trovata")
    return await db.gallery_images.find_one({"id": image_id}, {"_id": 0})


@router.post("/gallery/{image_id}/reject")
async def admin_reject_gallery_image(image_id: str, admin=Depends(require_admin)):
    db = get_db()
    res = await db.gallery_images.update_one(
        {"id": image_id},
        {"$set": {"status": "rejected", "updatedAt": datetime.now(timezone.utc).isoformat()}},
    )
    if not res.matched_count:
        raise HTTPException(404, "Immagine non trovata")
    return await db.gallery_images.find_one({"id": image_id}, {"_id": 0})


@router.delete("/gallery/{image_id}")
async def admin_delete_gallery_image(image_id: str, admin=Depends(require_admin)):
    db = get_db()
    await db.gallery_images.delete_one({"id": image_id})
    return {"ok": True}


@router.post("/gallery/sync-instagram")
async def admin_sync_instagram_gallery(
    sinceYear: int = 2021,
    admin=Depends(require_admin),
):
    """Importa tutte le foto Instagram dal sinceYear (esclude designazioni e reel)."""
    import os

    from ...instagram_gallery import parse_instagram_username, sync_instagram_gallery

    db = get_db()
    settings = await db.site_settings.find_one({"id": "site-settings"}, {"_id": 0, "instagramUrl": 1}) or {}
    session_id = os.getenv("INSTAGRAM_SESSION_ID", "").strip()
    if not session_id:
        raise HTTPException(
            status_code=400,
            detail="Configura INSTAGRAM_SESSION_ID sul server per sincronizzare da Instagram.",
        )
    username = parse_instagram_username(settings.get("instagramUrl") or "aia_legnano")
    return await sync_instagram_gallery(
        db,
        username=username,
        session_id=session_id,
        since_year=sinceYear,
        limit=0,
    )


@router.post("/gallery/import-instagram-batch")
async def admin_import_instagram_batch(payload: list[dict], admin=Depends(require_admin)):
    """Import batch da browser (imageDataUrl base64 + metadati post)."""
    from ...instagram_gallery import import_instagram_batch, parse_instagram_username

    db = get_db()
    settings = await db.site_settings.find_one({"id": "site-settings"}, {"_id": 0, "instagramUrl": 1}) or {}
    username = parse_instagram_username(settings.get("instagramUrl") or "aia_legnano")
    return await import_instagram_batch(db, payload, username=username)


@router.post("/gallery/upload")
async def admin_upload_gallery_image(
    file: UploadFile = File(...),
    caption: str = Form(""),
    sortOrder: int = Form(0),
    category: str = Form(""),
    sourceUrl: str = Form(""),
    aspect: str = Form("16:9"),
    admin=Depends(require_admin),
):
    from ...media_urls import resolve_media_url
    from ...gallery import save_uploaded_gallery_image

    _target, name, _size = await save_upload(
        file,
        allowed_ext=IMAGE_EXTENSIONS,
        max_bytes=DEFAULT_IMAGE_MAX_BYTES,
    )
    rel_path = f"/api/uploads/{name}"
    url = resolve_media_url(rel_path)
    db = get_db()
    return await save_uploaded_gallery_image(
        db,
        url=url,
        path=rel_path,
        caption=caption.strip(),
        sort_order=sortOrder,
        status="approved",
        source="admin",
        category=category.strip(),
        source_url=sourceUrl.strip() or url,
        aspect=aspect,
    )


