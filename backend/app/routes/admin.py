"""Admin routes - CRUD over all resources. Requires JWT admin token."""
import logging
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, Response
from slugify import slugify

from ..db import get_db
from ..security import require_admin, verify_password, create_token
from ..paths import UPLOAD_DIR
from ..models import (
    LoginRequest, TokenResponse, AdminInfo,
    SiteSettings, Page, Article, ArticleCreate, Event,
    Official, Member, MemberCreate, Designation, Lead, ContactMessage,
    Document, Album, Testimonial, UtilityPolo, UtilityItem, EventUtilityMaterialUpdate,
    DesignationSyncRequest, ArticleCategoryCreate,
    GalleryImage, GalleryImageCreate, GalleryImageUpdate,
)
from ..designations_sync import sync_from_aia_lombardia
from ..designations_import import import_designations_from_file, IMPORT_TEMPLATE_CSV
from ..designations_import_extract import SUPPORTED_EXTENSIONS
from ..members_import import import_members_from_file, IMPORT_TEMPLATE_CSV as MEMBERS_IMPORT_TEMPLATE_CSV
from ..sanitize import sanitize_html

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ---- Auth ----
@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    """
    Authenticate an admin user with email/password and issue a JWT.
    
    - **Body:** `{ "email": "...", "password": "..." }`
    - **Returns:** `TokenResponse` with `token` and admin info, or 401.
    - Use the token as `Authorization: Bearer <jwt_token>` on `/api/admin/*`.
    """
    db = get_db()
    admin = await db.admin_users.find_one({"email": payload.email.lower()}, {"_id": 0})
    if not admin or not verify_password(payload.password, admin["passwordHash"]):
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    token = create_token({"sub": admin["email"], "role": "admin", "name": admin.get("name", "Admin")})
    return TokenResponse(token=token, admin=AdminInfo(email=admin["email"], name=admin.get("name", "Admin")))


@router.get("/me")
async def me(admin=Depends(require_admin)):
    """
    Return the authenticated admin identity from the JWT.
    
    Requires JWT Bearer (admin). Returns `{email, name}`.
    """
    return {"email": admin.get("sub"), "name": admin.get("name", "Admin")}


# ---- Dashboard stats ----
@router.get("/dashboard")
async def dashboard(admin=Depends(require_admin)):
    """
    Admin dashboard aggregates: content counts, pending gallery/testimonials, leads, next event, designations.
    
    Requires JWT Bearer (admin).
    """
    from datetime import datetime, timezone

    from ..designation_enrich import build_member_lookups, enrich_designation
    from ..designation_filters import (
        current_season_label,
        designations_page_query,
        event_date_in_season_clause,
        merge_mongo_queries,
    )
    from ..media_urls import resolve_attachments
    from ..member_roles import legacy_arbitri_query

    db = get_db()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    season_clause = event_date_in_season_clause()
    event_q = merge_mongo_queries(season_clause, {"date": {"$gte": today}}) if season_clause else {"date": {"$gte": today}}
    next_rows = await db.events.find(event_q, {"_id": 0}).sort("date", 1).limit(1).to_list(1)
    next_event = None
    if next_rows:
        ev = next_rows[0]
        next_event = {**ev, "attachments": resolve_attachments(ev.get("attachments"))}

    settings = await db.site_settings.find_one({"id": "site-settings"}, {"_id": 0, "lastDesignationsSync": 1}) or {}
    des_q = designations_page_query(settings.get("lastDesignationsSync"))
    public_designations = await db.designations.find(des_q, {"_id": 0}).sort("matchDate", 1).limit(80).to_list(80)
    members = await db.members.find(
        legacy_arbitri_query(),
        {"_id": 0, "id": 1, "slug": 1, "firstName": 1, "lastName": 1, "kind": 1, "memberRole": 1},
    ).to_list(2000)
    slug_by_id, member_by_name = build_member_lookups(members)
    for item in public_designations:
        enrich_designation(item, slug_by_id, member_by_name)

    latest_rows = await db.comunicazioni_interne.find(
        {},
        {"_id": 0, "id": 1, "title": 1, "bodyHtml": 1, "createdAt": 1, "publishedAt": 1},
    ).sort("createdAt", -1).limit(1).to_list(1)
    latest_comunicazione = latest_rows[0] if latest_rows else None

    return {
        "articles": await db.articles.count_documents({}),
        "articlesPublished": await db.articles.count_documents({"status": "published"}),
        "articlesDraft": await db.articles.count_documents({"status": "draft"}),
        "pages": await db.pages.count_documents({}),
        "documents": await db.documents.count_documents({}),
        "events": await db.events.count_documents({}),
        "members": await db.members.count_documents({}),
        "designations": await db.designations.count_documents({}),
        "comunicazioni": await db.comunicazioni_interne.count_documents({}),
        "galleryApproved": await db.gallery_images.count_documents({"status": "approved"}),
        "galleryPending": await db.gallery_images.count_documents({"status": "pending"}),
        "testimonialsPending": await db.testimonials.count_documents({"status": "pending"}),
        "leadsNew": await db.leads.count_documents({"status": "new"}),
        "leadsTotal": await db.leads.count_documents({}),
        "messagesNew": await db.contact_messages.count_documents({"status": "new"}),
        "messagesTotal": await db.contact_messages.count_documents({}),
        "albums": await db.albums.count_documents({}),
        "menuPages": await db.pages.count_documents({"status": "published", "showInMenu": True}),
        "presenzeEventi": len(await db.presenze_evento.distinct("eventId")),
        "stagione": current_season_label(),
        "nextEvent": next_event,
        "publicDesignations": public_designations,
        "latestComunicazione": latest_comunicazione,
    }


# ---- Settings ----
@router.get("/settings")
async def admin_get_settings(admin=Depends(require_admin)):
    """Get settings.

`GET /settings`

Requires JWT Bearer (admin)."""
    db = get_db()
    doc = await db.site_settings.find_one({}, {"_id": 0})
    return doc or {}


@router.put("/settings")
async def admin_put_settings(payload: SiteSettings, admin=Depends(require_admin)):
    """Put settings.

`PUT /settings`

Params: **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    payload.updatedAt = datetime.now(timezone.utc).isoformat()
    doc = payload.model_dump()
    await db.site_settings.update_one({"id": "site-settings"}, {"$set": doc}, upsert=True)
    return doc


# ---- Pages ----
@router.get("/pages")
async def admin_list_pages(admin=Depends(require_admin)):
    """List pages.

`GET /pages`

Requires JWT Bearer (admin)."""
    db = get_db()
    pages = await db.pages.find({}, {"_id": 0}).to_list(200)
    pages.sort(key=lambda p: (0 if p.get("template") == "system" else 1, p.get("menuOrder", 100), p.get("title", "")))
    return pages


@router.post("/pages/reconcile-system")
async def admin_reconcile_system_pages(admin=Depends(require_admin)):
    """Crea/aggiorna le pagine di sistema mancanti o incomplete."""
    from ..seed import ensure_all_system_pages

    result = await ensure_all_system_pages()
    db = get_db()
    pages = await db.pages.find({}, {"_id": 0}).to_list(200)
    pages.sort(key=lambda p: (0 if p.get("template") == "system" else 1, p.get("menuOrder", 100), p.get("title", "")))
    return {"ok": True, **result, "pages": pages}


@router.post("/pages/{page_id}/reset-blocks")
async def admin_reset_page_blocks(page_id: str, admin=Depends(require_admin)):
    """Ripristina i blocchi predefiniti per la pagina (utile se il contenuto è stato svuotato)."""
    from ..seed import suggested_page_content

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
    """Get page.

`GET /pages/{page_id}`

Params: **page_id**.

Requires JWT Bearer (admin)."""
    db = get_db()
    p = await db.pages.find_one({"id": page_id}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Pagina non trovata")
    return p


@router.put("/pages/{page_id}")
async def admin_update_page(page_id: str, payload: Page, admin=Depends(require_admin)):
    """Update page.

`PUT /pages/{page_id}`

Params: **page_id**, **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    payload.id = page_id
    payload.bodyHtml = sanitize_html(payload.bodyHtml)
    from ..blocks_sanitize import sanitize_blocks
    payload.blocks = sanitize_blocks(payload.blocks)
    payload.updatedAt = datetime.now(timezone.utc).isoformat()
    doc = payload.model_dump()
    await db.pages.update_one({"id": page_id}, {"$set": doc}, upsert=True)
    return doc


@router.post("/pages")
async def admin_create_page(payload: Page, admin=Depends(require_admin)):
    """Create page.

`POST /pages`

Params: **payload**.

Requires JWT Bearer (admin)."""
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
    from ..blocks_sanitize import sanitize_blocks
    payload.blocks = sanitize_blocks(payload.blocks)
    doc = payload.model_dump()
    await db.pages.insert_one(doc.copy())
    return doc


@router.delete("/pages/{page_id}")
async def admin_delete_page(page_id: str, admin=Depends(require_admin)):
    """Delete page.

`DELETE /pages/{page_id}`

Params: **page_id**.

Requires JWT Bearer (admin)."""
    db = get_db()
    page = await db.pages.find_one({"id": page_id}, {"_id": 0})
    if not page:
        raise HTTPException(404, "Pagina non trovata")
    if page.get("template") == "system":
        raise HTTPException(400, "Le pagine di sistema non possono essere eliminate")
    await db.pages.delete_one({"id": page_id})
    return {"ok": True}


# ---- Articles ----
@router.get("/article-categories")
async def admin_list_article_categories(admin=Depends(require_admin)):
    """List article categories.

`GET /article-categories`

Requires JWT Bearer (admin)."""
    from ..article_categories import get_admin_article_categories

    db = get_db()
    return await get_admin_article_categories(db)


@router.post("/article-categories")
async def admin_add_article_category(payload: ArticleCategoryCreate, admin=Depends(require_admin)):
    """Add article category.

`POST /article-categories`

Params: **payload**.

Requires JWT Bearer (admin)."""
    from ..article_categories import add_article_category, normalize_category

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
    """List articles.

`GET /articles`

Requires JWT Bearer (admin)."""
    db = get_db()
    return await db.articles.find({}, {"_id": 0}).sort("publishedAt", -1).to_list(500)


@router.get("/articles/{article_id}")
async def admin_get_article(article_id: str, admin=Depends(require_admin)):
    """Get article.

`GET /articles/{article_id}`

Params: **article_id**.

Requires JWT Bearer (admin)."""
    from ..article_body import normalize_article_body_html
    from ..media_urls import resolve_media_fields

    db = get_db()
    a = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not a:
        raise HTTPException(404, "Articolo non trovato")
    a["bodyHtml"] = normalize_article_body_html(a.get("bodyHtml") or "")
    resolve_media_fields(a)
    return a


@router.post("/articles")
async def admin_create_article(payload: ArticleCreate, admin=Depends(require_admin)):
    """Create article.

`POST /articles`

Params: **payload**.

Requires JWT Bearer (admin)."""
    from ..article_categories import ensure_category_exists

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
    from ..gallery import sync_article_gallery

    await sync_article_gallery(db, doc)
    return doc


@router.put("/articles/{article_id}")
async def admin_update_article(article_id: str, payload: Article, admin=Depends(require_admin)):
    """Update article.

`PUT /articles/{article_id}`

Params: **article_id**, **payload**.

Requires JWT Bearer (admin)."""
    from ..article_categories import ensure_category_exists
    from ..article_sanitize import sanitize_article_html

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
    from ..gallery import sync_article_gallery

    await sync_article_gallery(db, doc)
    return doc


@router.delete("/articles/{article_id}")
async def admin_delete_article(article_id: str, admin=Depends(require_admin)):
    """Delete article.

`DELETE /articles/{article_id}`

Params: **article_id**.

Requires JWT Bearer (admin)."""
    db = get_db()
    await db.articles.delete_one({"id": article_id})
    from ..gallery import ARTICLE_GALLERY_SOURCES

    await db.gallery_images.delete_many(
        {"articleId": article_id, "source": {"$in": list(ARTICLE_GALLERY_SOURCES)}}
    )
    return {"ok": True}


@router.post("/articles/import-legacy")
async def admin_import_legacy_articles(admin=Depends(require_admin)):
    """Importa/aggiorna articoli da www.aia-legnano.it (WordPress)."""
    from ..legacy_article_import import run_legacy_article_import

    db = get_db()
    return await run_legacy_article_import(db, dry_run=False, download_images=True)


@router.post("/articles/cleanup-legacy")
async def admin_cleanup_legacy_articles(admin=Depends(require_admin)):
    """Rimuove articoli spazzatura e ricalcola tag associati (nome+cognome)."""
    from ..article_cleanup import run_article_cleanup

    db = get_db()
    return await run_article_cleanup(db)


# ---- Events ----
@router.get("/event-types")
async def admin_list_event_types(admin=Depends(require_admin)):
    """List event types.

`GET /event-types`

Requires JWT Bearer (admin)."""
    from ..event_categories import get_admin_event_types

    db = get_db()
    return await get_admin_event_types(db)


@router.post("/event-types")
async def admin_add_event_type(payload: ArticleCategoryCreate, admin=Depends(require_admin)):
    """Add event type.

`POST /event-types`

Params: **payload**.

Requires JWT Bearer (admin)."""
    from ..event_categories import add_event_type, normalize_event_type

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
    """List events.

`GET /events`

Requires JWT Bearer (admin)."""
    from ..designation_filters import event_date_in_season_clause

    db = get_db()
    q = event_date_in_season_clause() or {}
    return await db.events.find(q, {"_id": 0}).sort("date", -1).to_list(500)


@router.post("/events")
async def admin_create_event(payload: Event, admin=Depends(require_admin)):
    """Create event.

`POST /events`

Params: **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    from ..event_reminders import normalize_event_time
    from ..event_categories import ensure_event_type_exists

    doc = payload.model_dump()
    doc["orario"] = normalize_event_time(doc.get("orario"))
    doc["tipo"] = await ensure_event_type_exists(db, doc.get("tipo") or "Riunione")
    await db.events.insert_one(doc.copy())
    from ..event_reminders import schedule_event_created_notifications

    schedule_event_created_notifications(db, doc)
    return doc


@router.put("/events/{event_id}")
async def admin_update_event(event_id: str, payload: Event, admin=Depends(require_admin)):
    """Update event.

`PUT /events/{event_id}`

Params: **event_id**, **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    from ..event_reminders import normalize_event_time
    from ..event_categories import ensure_event_type_exists

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
    """Delete event.

`DELETE /events/{event_id}`

Params: **event_id**.

Requires JWT Bearer (admin)."""
    db = get_db()
    await db.events.delete_one({"id": event_id})
    return {"ok": True}


# ---- Officials ----
@router.get("/officials")
async def admin_list_officials(admin=Depends(require_admin)):
    """List officials.

`GET /officials`

Requires JWT Bearer (admin)."""
    db = get_db()
    return await db.officials.find({}, {"_id": 0}).sort("sortOrder", 1).to_list(100)


@router.post("/officials")
async def admin_create_official(payload: Official, admin=Depends(require_admin)):
    """Create official.

`POST /officials`

Params: **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    payload.bioHtml = sanitize_html(payload.bioHtml)
    doc = payload.model_dump()
    await db.officials.insert_one(doc.copy())
    return doc


@router.put("/officials/{official_id}")
async def admin_update_official(official_id: str, payload: Official, admin=Depends(require_admin)):
    """Update official.

`PUT /officials/{official_id}`

Params: **official_id**, **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    payload.id = official_id
    payload.bioHtml = sanitize_html(payload.bioHtml)
    doc = payload.model_dump()
    await db.officials.update_one({"id": official_id}, {"$set": doc})
    return doc


@router.delete("/officials/{official_id}")
async def admin_delete_official(official_id: str, admin=Depends(require_admin)):
    """Delete official.

`DELETE /officials/{official_id}`

Params: **official_id**.

Requires JWT Bearer (admin)."""
    db = get_db()
    await db.officials.delete_one({"id": official_id})
    return {"ok": True}


# ---- Members ----
@router.get("/members")
async def admin_list_members(memberRole: Optional[str] = None, admin=Depends(require_admin)):
    """List members.

`GET /members`

Params: **memberRole**.

Requires JWT Bearer (admin)."""
    db = get_db()
    from ..media_urls import resolve_media_fields
    from ..member_roles import normalize_member

    query = {"memberRole": memberRole} if memberRole else {}
    items = await db.members.find(query, {"_id": 0}).sort([("lastName", 1), ("firstName", 1)]).to_list(500)
    for item in items:
        normalize_member(item)
        resolve_media_fields(item)
    return items


@router.post("/members")
async def admin_create_member(payload: MemberCreate, admin=Depends(require_admin)):
    """Create member.

`POST /members`

Params: **payload**.

Requires JWT Bearer (admin)."""
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
    from ..member_roles import normalize_member

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
    normalize_member(doc)
    await db.members.insert_one(doc.copy())
    from ..portal_credentials import ensure_member_portal_credentials

    await ensure_member_portal_credentials(doc)
    return doc


@router.put("/members/{member_id}")
async def admin_update_member(member_id: str, payload: Member, admin=Depends(require_admin)):
    """Update member.

`PUT /members/{member_id}`

Params: **member_id**, **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    payload.id = member_id
    payload.updatedAt = datetime.now(timezone.utc).isoformat()
    from ..member_roles import normalize_member

    payload.bio = (payload.bio or "").strip()
    payload.chiSiamoText = (payload.chiSiamoText or "").strip()
    payload.presidentLongBio = (payload.presidentLongBio or "").strip()
    payload.bioHtml = ""
    if payload.memberRole:
        payload.memberRole = payload.memberRole.strip().lower()
    if not (payload.slug or "").strip():
        payload.slug = slugify(f"{payload.firstName}-{payload.lastName}")
    doc = payload.model_dump()
    normalize_member(doc)
    await db.members.update_one({"id": member_id}, {"$set": doc})
    from ..media_urls import resolve_media_fields
    from ..member_category import refresh_member_category

    if doc.get("memberRole") == "arbitro":
        await refresh_member_category(db, doc, persist=True)
    resolve_media_fields(doc)
    from ..portal_credentials import ensure_member_portal_credentials

    await ensure_member_portal_credentials(doc)
    return doc


@router.delete("/members/{member_id}")
async def admin_delete_member(member_id: str, admin=Depends(require_admin)):
    """Delete member.

`DELETE /members/{member_id}`

Params: **member_id**.

Requires JWT Bearer (admin)."""
    db = get_db()
    await db.members.delete_one({"id": member_id})
    return {"ok": True}


@router.get("/members/import-template")
async def admin_members_import_template(admin=Depends(require_admin)):
    """Members import template.

`GET /members/import-template`

Requires JWT Bearer (admin)."""
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


# ---- Designations ----
def _designation_list_query() -> dict:
    from ..designation_filters import (
        current_season_label,
        match_date_in_season_clause,
        merge_mongo_queries,
    )

    return merge_mongo_queries(
        {"role": {"$not": {"$regex": "osservatore", "$options": "i"}}},
        match_date_in_season_clause(current_season_label()),
    )


async def _validate_designation_payload(db, doc: dict) -> None:
    from ..member_roles import is_observer_designation_role, has_designations, normalize_member

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
    """List designations.

`GET /designations`

Requires JWT Bearer (admin)."""
    db = get_db()
    items = await db.designations.find(_designation_list_query(), {"_id": 0}).sort("matchDate", -1).to_list(500)
    from ..designation_enrich import build_member_lookups, enrich_designation
    from ..member_roles import legacy_arbitri_query

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
    """Create designation.

`POST /designations`

Params: **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    doc = payload.model_dump()
    await _validate_designation_payload(db, doc)
    doc = await _attach_member_slug(db, doc)
    await db.designations.insert_one(doc.copy())
    return doc


@router.put("/designations/{des_id}")
async def admin_update_designation(des_id: str, payload: Designation, admin=Depends(require_admin)):
    """Update designation.

`PUT /designations/{des_id}`

Params: **des_id**, **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    payload.id = des_id
    doc = payload.model_dump()
    await _validate_designation_payload(db, doc)
    doc = await _attach_member_slug(db, doc)
    await db.designations.update_one({"id": des_id}, {"$set": doc})
    return doc


@router.delete("/designations/{des_id}")
async def admin_delete_designation(des_id: str, admin=Depends(require_admin)):
    """Delete designation.

`DELETE /designations/{des_id}`

Params: **des_id**.

Requires JWT Bearer (admin)."""
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
    """Designations sync status.

`GET /designations/sync-status`

Requires JWT Bearer (admin)."""
    db = get_db()
    settings = await db.site_settings.find_one({"id": "site-settings"}, {"_id": 0, "lastDesignationsSync": 1})
    return settings.get("lastDesignationsSync") if settings else {}


# ---- Leads ----
@router.get("/leads")
async def admin_list_leads(admin=Depends(require_admin)):
    """List leads.

`GET /leads`

Requires JWT Bearer (admin)."""
    db = get_db()
    return await db.leads.find({}, {"_id": 0}).sort("createdAt", -1).to_list(1000)


@router.put("/leads/{lead_id}")
async def admin_update_lead_status(lead_id: str, payload: dict, admin=Depends(require_admin)):
    """Update lead status.

`PUT /leads/{lead_id}`

Params: **lead_id**, **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    status = payload.get("status", "new")
    await db.leads.update_one({"id": lead_id}, {"$set": {"status": status}})
    return {"ok": True}


@router.delete("/leads/{lead_id}")
async def admin_delete_lead(lead_id: str, admin=Depends(require_admin)):
    """Delete lead.

`DELETE /leads/{lead_id}`

Params: **lead_id**.

Requires JWT Bearer (admin)."""
    db = get_db()
    await db.leads.delete_one({"id": lead_id})
    return {"ok": True}


# ---- Messages ----
@router.get("/messages")
async def admin_list_messages(admin=Depends(require_admin)):
    """List messages.

`GET /messages`

Requires JWT Bearer (admin)."""
    db = get_db()
    return await db.contact_messages.find({}, {"_id": 0}).sort("createdAt", -1).to_list(1000)


@router.put("/messages/{msg_id}")
async def admin_update_message(msg_id: str, payload: dict, admin=Depends(require_admin)):
    """Update message.

`PUT /messages/{msg_id}`

Params: **msg_id**, **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    status = payload.get("status", "new")
    await db.contact_messages.update_one({"id": msg_id}, {"$set": {"status": status}})
    return {"ok": True}


@router.delete("/messages/{msg_id}")
async def admin_delete_message(msg_id: str, admin=Depends(require_admin)):
    """Delete message.

`DELETE /messages/{msg_id}`

Params: **msg_id**.

Requires JWT Bearer (admin)."""
    db = get_db()
    await db.contact_messages.delete_one({"id": msg_id})
    return {"ok": True}


# ---- Documents (downloads) ----
@router.get("/documents")
async def admin_list_documents(admin=Depends(require_admin)):
    """List documents.

`GET /documents`

Requires JWT Bearer (admin)."""
    from ..media_urls import file_size_label_for_media_url

    db = get_db()
    docs = await db.documents.find({}, {"_id": 0}).sort("sortOrder", 1).to_list(500)
    for d in docs:
        if not (d.get("fileSize") or "").strip() and d.get("fileUrl"):
            label = file_size_label_for_media_url(d["fileUrl"])
            if label:
                d["fileSize"] = label
    return docs


async def _enrich_document(doc: dict) -> dict:
    from ..document_sections import ensure_section_exists, normalize_document_category
    from ..media_urls import file_size_label_for_media_url

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
    """List document sections.

`GET /document-sections`

Requires JWT Bearer (admin)."""
    from ..document_sections import get_admin_document_sections

    db = get_db()
    return await get_admin_document_sections(db)


@router.post("/document-sections")
async def admin_add_document_section(payload: ArticleCategoryCreate, admin=Depends(require_admin)):
    """Add document section.

`POST /document-sections`

Params: **payload**.

Requires JWT Bearer (admin)."""
    from ..document_sections import add_document_section, normalize_section_name

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
    """Create document.

`POST /documents`

Params: **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    doc = await _enrich_document(payload.model_dump())
    await db.documents.insert_one(doc.copy())
    return doc


@router.put("/documents/{doc_id}")
async def admin_update_document(doc_id: str, payload: Document, admin=Depends(require_admin)):
    """Update document.

`PUT /documents/{doc_id}`

Params: **doc_id**, **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    payload.id = doc_id
    doc = await _enrich_document(payload.model_dump())
    await db.documents.update_one({"id": doc_id}, {"$set": doc})
    return doc


@router.delete("/documents/{doc_id}")
async def admin_delete_document(doc_id: str, admin=Depends(require_admin)):
    """Delete document.

`DELETE /documents/{doc_id}`

Params: **doc_id**.

Requires JWT Bearer (admin)."""
    db = get_db()
    await db.documents.delete_one({"id": doc_id})
    return {"ok": True}


# ---- Utility (area associati) ----
_UTILITY_SECTIONS = {"link_utili"}


@router.get("/utility")
async def admin_get_utility(admin=Depends(require_admin)):
    """Get utility.

`GET /utility`

Requires JWT Bearer (admin)."""
    from ..designation_filters import event_date_in_season_clause, merge_mongo_queries

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
    """Update utility polo.

`PUT /utility/polo`

Params: **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    polo = payload.model_dump()
    await db.site_settings.update_one(
        {"id": "site-settings"},
        {"$set": {"utilityPolo": polo}},
        upsert=True,
    )
    return polo


@router.post("/utility-items")
async def admin_create_utility_item(payload: UtilityItem, admin=Depends(require_admin)):
    """Create utility item.

`POST /utility-items`

Params: **payload**.

Requires JWT Bearer (admin)."""
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
    """Update utility item.

`PUT /utility-items/{item_id}`

Params: **item_id**, **payload**.

Requires JWT Bearer (admin)."""
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
    """Delete utility item.

`DELETE /utility-items/{item_id}`

Params: **item_id**.

Requires JWT Bearer (admin)."""
    db = get_db()
    await db.utility_items.delete_one({"id": item_id})
    return {"ok": True}


@router.get("/utility/event/{event_id}")
@router.get("/utility/rto/{event_id}")
async def admin_get_utility_event_material(event_id: str, admin=Depends(require_admin)):
    """Get utility event material.

`GET /utility/event/{event_id}`

Params: **event_id**.

Requires JWT Bearer (admin)."""
    from ..media_urls import resolve_attachments

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
    """Update utility event material.

`PUT /utility/event/{event_id}/material`

Params: **event_id**, **payload**.

Requires JWT Bearer (admin)."""
    from ..media_urls import resolve_attachments

    db = get_db()
    ev = await db.events.find_one({"id": event_id}, {"_id": 0, "id": 1})
    if not ev:
        raise HTTPException(status_code=404, detail="Evento non trovato")
    material = [a.model_dump() for a in (payload.utilityMaterial or [])]
    await db.events.update_one({"id": event_id}, {"$set": {"utilityMaterial": material}})
    return {"ok": True, "utilityMaterial": resolve_attachments(material)}


@router.post("/documents/import-aia-figc")
async def admin_import_aia_documents(admin=Depends(require_admin)):
    """Importa o aggiorna i documenti da https://www.aia-figc.it/download/"""
    from ..scrapers.aia_downloads import import_aia_downloads

    db = get_db()
    result = await import_aia_downloads(db, download_files=True, replace_existing=True)
    return {"ok": True, **result}


@router.post("/documents/import-aia-legnano")
async def admin_import_legnano_documents(admin=Depends(require_admin)):
    """Importa o aggiorna i documenti da https://www.aia-legnano.it/download/"""
    from ..scrapers.aia_legnano_downloads import import_legnano_downloads

    db = get_db()
    result = await import_legnano_downloads(db, download_files=True, replace_existing=True)
    return {"ok": True, **result}


@router.post("/documents/import-all-sources")
async def admin_import_all_documents(admin=Depends(require_admin)):
    """Importa documenti da AIA FIGC e AIA Legnano."""
    from ..scrapers.aia_downloads import import_aia_downloads
    from ..scrapers.aia_legnano_downloads import import_legnano_downloads

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


# ---- Albums ----
@router.get("/albums")
async def admin_list_albums(admin=Depends(require_admin)):
    """List albums.

`GET /albums`

Requires JWT Bearer (admin)."""
    db = get_db()
    return await db.albums.find({}, {"_id": 0}).sort("sortOrder", 1).to_list(200)


@router.post("/albums")
async def admin_create_album(payload: Album, admin=Depends(require_admin)):
    """Create album.

`POST /albums`

Params: **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    if not payload.slug:
        payload.slug = slugify(payload.title)
    doc = payload.model_dump()
    await db.albums.insert_one(doc.copy())
    return doc


@router.put("/albums/{album_id}")
async def admin_update_album(album_id: str, payload: Album, admin=Depends(require_admin)):
    """Update album.

`PUT /albums/{album_id}`

Params: **album_id**, **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    payload.id = album_id
    doc = payload.model_dump()
    await db.albums.update_one({"id": album_id}, {"$set": doc})
    return doc


@router.delete("/albums/{album_id}")
async def admin_delete_album(album_id: str, admin=Depends(require_admin)):
    """Delete album.

`DELETE /albums/{album_id}`

Params: **album_id**.

Requires JWT Bearer (admin)."""
    db = get_db()
    await db.albums.delete_one({"id": album_id})
    return {"ok": True}


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
    """List testimonials.

`GET /testimonials`

Requires JWT Bearer (admin)."""
    db = get_db()
    return await db.testimonials.find({}, {"_id": 0}).sort("sortOrder", 1).to_list(100)


@router.post("/testimonials")
async def admin_create_testimonial(payload: Testimonial, admin=Depends(require_admin)):
    """Create testimonial.

`POST /testimonials`

Params: **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    doc = await _attach_testimonial_member(db, payload.model_dump())
    await db.testimonials.insert_one(doc.copy())
    return doc


@router.put("/testimonials/{t_id}")
async def admin_update_testimonial(t_id: str, payload: Testimonial, admin=Depends(require_admin)):
    """Update testimonial.

`PUT /testimonials/{t_id}`

Params: **t_id**, **payload**.

Requires JWT Bearer (admin)."""
    db = get_db()
    payload.id = t_id
    doc = await _attach_testimonial_member(db, payload.model_dump())
    await db.testimonials.update_one({"id": t_id}, {"$set": doc})
    return doc


@router.delete("/testimonials/{t_id}")
async def admin_delete_testimonial(t_id: str, admin=Depends(require_admin)):
    """Delete testimonial.

`DELETE /testimonials/{t_id}`

Params: **t_id**.

Requires JWT Bearer (admin)."""
    from ..seed import _set_seed_flag

    db = get_db()
    await db.testimonials.delete_one({"id": t_id})
    if await db.testimonials.count_documents({}) == 0:
        await _set_seed_flag("testimonials")
    return {"ok": True}


# ---- Galleria (immagini sito) ----
@router.get("/gallery")
async def admin_list_gallery(
    status: Optional[str] = None,
    category: Optional[str] = None,
    dateFrom: Optional[str] = None,
    dateTo: Optional[str] = None,
    admin=Depends(require_admin),
):
    """List gallery.

`GET /gallery`

Params: **status**, **category**, **dateFrom**, **dateTo**.

Requires JWT Bearer (admin)."""
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
    """Create gallery image.

`POST /gallery`

Params: **payload**.

Requires JWT Bearer (admin)."""
    from ..article_categories import ensure_category_exists
    from ..gallery import save_uploaded_gallery_image

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
    from ..media_urls import public_api_base, resolve_media_url

    db = get_db()
    doc = await db.gallery_images.find_one({"id": image_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Immagine non trovata")
    src = (doc.get("sourceUrl") or doc.get("url") or doc.get("path") or "").strip()
    if not src:
        raise HTTPException(404, "Sorgente non disponibile")

    def _local_upload_response(path_value: str) -> FileResponse | None:
        name = path_value.rstrip("/").split("/")[-1]
        if not name:
            return None
        local = UPLOAD_DIR / name
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
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                r = await client.get(resolved)
                r.raise_for_status()
            except httpx.HTTPError as exc:
                raise HTTPException(502, f"Impossibile scaricare l'immagine: {exc}") from exc
            ctype = r.headers.get("content-type", "image/jpeg")
            return Response(content=r.content, media_type=ctype)

    raise HTTPException(404, "File non trovato")


@router.put("/gallery/{image_id}")
async def admin_update_gallery_image(
    image_id: str, payload: GalleryImageUpdate, admin=Depends(require_admin)
):
    """Update gallery image.

`PUT /gallery/{image_id}`

Params: **image_id**, **payload**.

Requires JWT Bearer (admin)."""
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
        from ..article_categories import ensure_category_exists

        upd["category"] = await ensure_category_exists(db, payload.category) if payload.category else ""
    if payload.url is not None:
        upd["url"] = payload.url
    if payload.path is not None:
        upd["path"] = payload.path
    if payload.sourceUrl is not None:
        upd["sourceUrl"] = payload.sourceUrl
    if payload.aspect is not None:
        from ..gallery import _normalize_aspect

        upd["aspect"] = _normalize_aspect(payload.aspect)
    if payload.memberIds is not None:
        upd["memberIds"] = list(payload.memberIds)
    if payload.url is not None or payload.path is not None or payload.aspect is not None:
        upd["cropEdited"] = True
    await db.gallery_images.update_one({"id": image_id}, {"$set": upd})
    return await db.gallery_images.find_one({"id": image_id}, {"_id": 0})


@router.post("/gallery/{image_id}/approve")
async def admin_approve_gallery_image(image_id: str, admin=Depends(require_admin)):
    """Approve gallery image.

`POST /gallery/{image_id}/approve`

Params: **image_id**.

Requires JWT Bearer (admin)."""
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
    """Reject gallery image.

`POST /gallery/{image_id}/reject`

Params: **image_id**.

Requires JWT Bearer (admin)."""
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
    """Delete gallery image.

`DELETE /gallery/{image_id}`

Params: **image_id**.

Requires JWT Bearer (admin)."""
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

    from ..instagram_gallery import parse_instagram_username, sync_instagram_gallery

    db = get_db()
    settings = await db.settings.find_one({"_id": "site"}, {"_id": 0, "instagramUrl": 1}) or {}
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
    from ..instagram_gallery import import_instagram_batch, parse_instagram_username

    db = get_db()
    settings = await db.settings.find_one({"_id": "site"}, {"_id": 0, "instagramUrl": 1}) or {}
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
    """Upload gallery image.

`POST /gallery/upload`

Params: **caption**, **sortOrder**, **category**, **sourceUrl**, **aspect**.

Requires JWT Bearer (admin)."""
    import uuid as _u
    from ..media_urls import resolve_media_url
    from ..gallery import save_uploaded_gallery_image

    ext = Path(file.filename or "").suffix.lower() or ".bin"
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        raise HTTPException(400, "Formato non supportato")
    name = f"{_u.uuid4().hex}{ext}"
    target = UPLOAD_DIR / name
    with target.open("wb") as f:
        shutil.copyfileobj(file.file, f)
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


# ---- Upload ----
@router.post("/upload")
async def admin_upload(file: UploadFile = File(...), admin=Depends(require_admin)):
    """Upload.

`POST /upload`

Requires JWT Bearer (admin)."""
    import uuid as _u
    ext = Path(file.filename or "").suffix.lower() or ".bin"
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}:
        raise HTTPException(400, "Formato non supportato")
    name = f"{_u.uuid4().hex}{ext}"
    target = UPLOAD_DIR / name
    with target.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    from ..media_urls import resolve_media_url

    rel_path = f"/api/uploads/{name}"
    abs_url = resolve_media_url(rel_path)
    # Persist record
    db = get_db()
    doc = {
        "id": _u.uuid4().hex,
        "filename": file.filename,
        "path": rel_path,
        "url": abs_url,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    await db.media.insert_one(doc.copy())
    return doc


@router.post("/upload-attachment")
async def admin_upload_attachment(file: UploadFile = File(...), admin=Depends(require_admin)):
    """Upload attachment.

`POST /upload-attachment`

Requires JWT Bearer (admin)."""
    import uuid as _u

    allowed = {
        ".jpg", ".jpeg", ".png", ".webp", ".gif",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".zip",
        ".mp4", ".webm", ".mov",
    }
    video_ext = {".mp4", ".webm", ".mov"}
    ext = Path(file.filename or "").suffix.lower() or ".bin"
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Formato file non supportato")
    max_bytes = 50 * 1024 * 1024 if ext in video_ext else 10 * 1024 * 1024
    name = f"att_{_u.uuid4().hex}{ext}"
    target = UPLOAD_DIR / name
    with target.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    if target.stat().st_size > max_bytes:
        target.unlink(missing_ok=True)
        limit_mb = max_bytes // (1024 * 1024)
        raise HTTPException(status_code=400, detail=f"File troppo grande (max {limit_mb} MB)")
    from ..media_urls import resolve_media_url

    rel_path = f"/api/uploads/{name}"
    return {
        "id": _u.uuid4().hex,
        "fileName": file.filename or name,
        "fileUrl": rel_path,
        "url": resolve_media_url(rel_path),
        "fileSize": target.stat().st_size,
        "mimeType": file.content_type or "",
    }


@router.get("/media")
async def admin_list_media(admin=Depends(require_admin)):
    """List media.

`GET /media`

Requires JWT Bearer (admin)."""
    db = get_db()
    return await db.media.find({}, {"_id": 0}).sort("createdAt", -1).to_list(500)


# ---- Comunicazioni interne (registro letture) ----
@router.get("/comunicazioni/{comm_id}/letture")
async def admin_comunicazione_letture(comm_id: str, admin=Depends(require_admin)):
    """Comunicazione letture.

`GET /comunicazioni/{comm_id}/letture`

Params: **comm_id**.

Requires JWT Bearer (admin)."""
    from ..comunicazioni_helpers import comunicazione_letture_report

    db = get_db()
    c = await db.comunicazioni_interne.find_one({"id": comm_id}, {"_id": 0})
    if not c:
        raise HTTPException(status_code=404, detail="Comunicazione non trovata")
    return await comunicazione_letture_report(db, c)
