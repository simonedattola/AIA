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

# ---- Dashboard stats ----
@router.get("/dashboard")
async def dashboard(admin=Depends(require_admin)):
    from datetime import datetime, timezone

    from ...designation_enrich import build_member_lookups, enrich_designation
    from ...designation_filters import (
        current_season_label,
        designations_page_query,
        event_date_in_season_clause,
        merge_mongo_queries,
    )
    from ...media_urls import resolve_attachments
    from ...member_roles import legacy_arbitri_query

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


