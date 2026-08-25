"""Public API routes - readable without authentication."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional

from ..db import get_db
from ..designation_enrich import (
    build_member_lookups,
    enrich_designation,
    enrich_testimonial,
)
from ..designation_queries import member_designations_query
from ..member_roles import (
    normalize_member,
    public_member,
    legacy_arbitri_query,
    legacy_chi_siamo_query,
    is_observer_designation_role,
)
from ..media_urls import resolve_media_fields, resolve_attachments
from ..sanitize import sanitize_html
from ..page_nav import page_to_nav_item
from ..models import (
    LeadCreate,
    Lead,
    ContactCreate,
    ContactMessage,
)
from ..mailer import (
    send_email,
    render_lead_email,
    render_lead_confirmation_email,
    render_contact_email,
)
from ..staff_email import staff_notify_email
from ..person_names import format_person_name
import os

router = APIRouter(prefix="/api/public", tags=["public"])


def _normalize_nav_item(item: dict) -> dict:
    """Associati → Arbitri nel menu pubblico (route attuale /arbitri)."""
    if (
        item.get("highlight")
        or "area-associati" in (item.get("href") or "")
        or "area-riservata" in (item.get("href") or "")
    ):
        return item
    href = item.get("href") or ""
    label = (item.get("label") or "").strip()
    if href in ("/associati", "/associati/"):
        return {**item, "href": "/arbitri", "label": "Arbitri"}
    if href == "/arbitri" and label.lower() == "associati":
        return {**item, "label": "Arbitri"}
    return item


@router.get("/settings")
async def get_settings():
    db = get_db()
    doc = await db.site_settings.find_one({"id": "site-settings"}, {"_id": 0})
    if not doc:
        doc = await db.site_settings.find_one({}, {"_id": 0})
    return doc or {}


@router.get("/nav")
async def get_nav():
    db = get_db()
    pages = (
        await db.pages.find(
            {"status": "published", "showInMenu": True},
            {
                "_id": 0,
                "slug": 1,
                "menuLabel": 1,
                "title": 1,
                "menuOrder": 1,
                "menuHighlight": 1,
            },
        )
        .sort("menuOrder", 1)
        .to_list(100)
    )
    items = [page_to_nav_item(p) for p in pages]
    items.sort(key=lambda x: x.get("order", 100))
    return [_normalize_nav_item(it) for it in items]


@router.get("/pages/{slug}")
async def get_page(slug: str):
    db = get_db()
    page = await db.pages.find_one({"slug": slug, "status": "published"}, {"_id": 0})
    if not page:
        raise HTTPException(status_code=404, detail="Pagina non trovata")
    return page


@router.get("/articles")
async def list_articles(category: Optional[str] = None, limit: int = 20, skip: int = 0):
    db = get_db()
    q = {"status": "published", "portalOnly": {"$ne": True}}
    if category:
        q["category"] = category
    total = await db.articles.count_documents(q)
    items = (
        await db.articles.find(q, {"_id": 0})
        .sort("publishedAt", -1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )
    for item in items:
        resolve_media_fields(item)
    return {"items": items, "total": total}


@router.get("/articles/{slug}")
async def get_article(slug: str):
    db = get_db()
    art = await db.articles.find_one(
        {"slug": slug, "status": "published", "portalOnly": {"$ne": True}},
        {"_id": 0},
    )
    if not art:
        raise HTTPException(status_code=404, detail="Articolo non trovato")
    from ..article_body import normalize_article_body_html
    from ..article_member_match import (
        apply_auto_related_members,
        linkify_member_names_in_html,
    )
    from ..gallery_member_tags import load_members_for_match
    from ..person_names import format_person_name

    art["bodyHtml"] = normalize_article_body_html(art.get("bodyHtml") or "")
    members = await load_members_for_match(db)
    related_ids = apply_auto_related_members(art, members)
    by_id = {m["id"]: m for m in members if m.get("id")}
    related_members = []
    for mid in related_ids:
        m = by_id.get(mid)
        if not m or not (m.get("slug") or "").strip():
            continue
        related_members.append(
            {
                "id": mid,
                "slug": m["slug"],
                "firstName": m.get("firstName") or "",
                "lastName": m.get("lastName") or "",
                "name": format_person_name(m.get("firstName"), m.get("lastName")),
            }
        )
    if related_ids != (art.get("relatedMemberIds") or []):
        # Lazy persist so next profile/gallery sync sees the tags
        await db.articles.update_one(
            {"id": art["id"]},
            {"$set": {"relatedMemberIds": related_ids}},
        )
        art["relatedMemberIds"] = related_ids
    art["bodyHtml"] = linkify_member_names_in_html(art.get("bodyHtml") or "", members)
    art["relatedMembers"] = related_members
    resolve_media_fields(art)
    related = (
        await db.articles.find(
            {"status": "published", "category": art["category"], "slug": {"$ne": slug}},
            {
                "_id": 0,
                "slug": 1,
                "title": 1,
                "excerpt": 1,
                "coverUrl": 1,
                "publishedAt": 1,
                "category": 1,
            },
        )
        .sort("publishedAt", -1)
        .limit(3)
        .to_list(3)
    )
    for r in related:
        resolve_media_fields(r)
    return {"article": art, "related": related}


@router.get("/categories")
async def list_categories():
    from ..article_categories import get_public_article_categories

    db = get_db()
    return await get_public_article_categories(db)


@router.get("/events")
async def list_events(upcoming: bool = False, limit: int = 50):
    db = get_db()
    from ..event_access import public_events_query

    today = ""
    if upcoming:
        from datetime import datetime, timezone

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    q = public_events_query(upcoming=upcoming, today=today)
    items = (
        await db.events.find(q, {"_id": 0})
        .sort("date", 1 if upcoming else -1)
        .limit(limit)
        .to_list(limit)
    )
    for item in items:
        item["attachments"] = resolve_attachments(item.get("attachments"))
    return items


@router.get("/officials")
async def list_officials():
    from ..person_names import format_person_name_parts

    db = get_db()
    items = await db.officials.find({}, {"_id": 0}).sort("sortOrder", 1).to_list(100)
    for item in items:
        first, last = format_person_name_parts(
            item.get("firstName"), item.get("lastName")
        )
        if first:
            item["firstName"] = first
        if last:
            item["lastName"] = last
        resolve_media_fields(item)
    return items


@router.get("/members")
async def list_members(
    q: Optional[str] = None,
    category: Optional[str] = None,
    memberRole: Optional[str] = None,
    scope: Optional[str] = None,
    limit: int = 200,
):
    """Lista membri. Default: arbitri+assistenti+benemeriti. scope=chi_siamo per organigramma."""
    db = get_db()
    if memberRole in ("osservatore", "osservatori"):
        from ..member_roles import osservatori_query

        query = osservatori_query()
    elif memberRole:
        query = {"memberRole": memberRole}
    elif scope in ("chi_siamo", "organigramma"):
        query = legacy_chi_siamo_query()
    elif scope in ("osservatori", "osservatore"):
        from ..member_roles import osservatori_query

        query = osservatori_query()
    else:
        query = legacy_arbitri_query()
    if category:
        query["category"] = category
    if q:
        query["$or"] = [
            {"firstName": {"$regex": q, "$options": "i"}},
            {"lastName": {"$regex": q, "$options": "i"}},
        ]
    from ..member_category import refresh_member_category
    from ..member_roles import can_have_max_category

    items = (
        await db.members.find(query, {"_id": 0})
        .sort([("lastName", 1), ("firstName", 1)])
        .limit(limit)
        .to_list(limit)
    )
    for item in items:
        normalize_member(item)
        if can_have_max_category(item):
            await refresh_member_category(db, item, persist=True)
        resolve_media_fields(item)
        public_member(item)
    return items


@router.get("/members/{slug}")
async def get_member(slug: str, season: Optional[str] = None):
    db = get_db()
    m = await db.members.find_one({"slug": slug}, {"_id": 0})
    if not m:
        raise HTTPException(status_code=404, detail="Profilo non trovato")
    normalize_member(m)
    resolve_media_fields(m)
    mid = m["id"]
    awards = sorted(m.get("awards") or [], key=lambda a: a.get("sortOrder", 0))

    from ..designation_filters import current_season_label, distinct_seasons_from_dates

    designations = []
    seasons_available: list[str] = []
    query_all = member_designations_query(m, season=None)
    if query_all:
        date_rows = await db.designations.find(
            query_all, {"_id": 0, "matchDate": 1}
        ).to_list(2000)
        seasons_available = distinct_seasons_from_dates(
            [d.get("matchDate", "") for d in date_rows]
        )
    active_season = season or (
        seasons_available[0] if seasons_available else current_season_label()
    )
    des_q = member_designations_query(m, season=active_season)
    if des_q:
        designations = (
            await db.designations.find(des_q, {"_id": 0})
            .sort("matchDate", -1)
            .limit(1000)
            .to_list(1000)
        )
        slug_val = (m.get("slug") or "").strip()
        for d in designations:
            updates = {}
            if d.get("memberId") != mid:
                updates["memberId"] = mid
            if slug_val and (d.get("memberSlug") or "") != slug_val:
                updates["memberSlug"] = slug_val
            if updates:
                await db.designations.update_one({"id": d["id"]}, {"$set": updates})
                d.update(updates)
    members = await db.members.find(
        legacy_arbitri_query(),
        {
            "_id": 0,
            "id": 1,
            "slug": 1,
            "firstName": 1,
            "lastName": 1,
            "kind": 1,
            "memberRole": 1,
        },
    ).to_list(2000)
    slug_by_id, member_by_name = build_member_lookups(members)
    for item in designations:
        enrich_designation(item, slug_by_id, member_by_name)

    from ..member_category import refresh_member_category
    from ..member_roles import can_have_max_category

    if can_have_max_category(m):
        await refresh_member_category(db, m, persist=True)

    article_fields = {
        "_id": 0,
        "slug": 1,
        "title": 1,
        "category": 1,
        "excerpt": 1,
        "coverUrl": 1,
        "publishedAt": 1,
    }
    articles = (
        await db.articles.find(
            {"status": "published", "relatedMemberIds": mid},
            article_fields,
        )
        .sort("publishedAt", -1)
        .limit(24)
        .to_list(24)
    )

    events = (
        await db.events.find(
            {
                "$or": [
                    {"invitedMemberIds": mid},
                    {"relatedMemberIds": mid},
                ]
            },
            {
                "_id": 0,
                "id": 1,
                "date": 1,
                "titolo": 1,
                "descrizione": 1,
                "luogo": 1,
                "tipo": 1,
            },
        )
        .sort("date", -1)
        .limit(12)
        .to_list(12)
    )

    testimonials = (
        await db.testimonials.find(
            {
                "memberId": mid,
                "$or": [{"status": "published"}, {"status": {"$exists": False}}],
            },
            {"_id": 0, "id": 1, "name": 1, "role": 1, "quote": 1, "photoUrl": 1},
        )
        .sort("sortOrder", 1)
        .to_list(10)
    )
    for a in articles:
        resolve_media_fields(a)
    mem_photo = (m.get("photoUrl") or "").strip()
    for t in testimonials:
        if not (t.get("photoUrl") or "").strip() and mem_photo:
            t["photoUrl"] = mem_photo
        resolve_media_fields(t)

    return {
        "member": public_member(m),
        "awards": awards,
        "articles": articles,
        "events": events,
        "testimonials": testimonials,
        "designations": designations,
        "seasonsAvailable": seasons_available,
        "activeSeason": active_season,
    }


@router.get("/designations")
async def list_designations(
    role: Optional[str] = None, category: Optional[str] = None, limit: int = 500
):
    db = get_db()
    from ..designation_filters import designations_page_query

    settings = (
        await db.site_settings.find_one(
            {"id": "site-settings"}, {"_id": 0, "lastDesignationsSync": 1}
        )
        or {}
    )
    last_sync = settings.get("lastDesignationsSync")
    query = designations_page_query(last_sync)
    if role:
        if role == "Assistente":
            query["$and"].append({"role": {"$regex": r"^Assistente", "$options": "i"}})
        else:
            query["$and"].append({"role": role})
    if category:
        query["$and"].append(
            {"$or": [{"championship": category}, {"category": category}]}
        )
    items = (
        await db.designations.find(query, {"_id": 0})
        .sort("matchDate", 1)
        .limit(limit)
        .to_list(limit)
    )

    members = await db.members.find(
        legacy_arbitri_query(),
        {
            "_id": 0,
            "id": 1,
            "slug": 1,
            "firstName": 1,
            "lastName": 1,
            "kind": 1,
            "memberRole": 1,
        },
    ).to_list(2000)
    slug_by_id, member_by_name = build_member_lookups(members)
    for item in items:
        enrich_designation(item, slug_by_id, member_by_name)
    return items


@router.get("/stats")
async def get_stats():
    db = get_db()
    members_total = await db.members.count_documents({})
    associati = await db.members.count_documents({})
    osservatori = await db.members.count_documents(
        {
            "$or": [
                {"memberRole": "osservatore"},
                {
                    "memberRole": {"$exists": False},
                    "kind": {"$in": ["oa", "ot", "osservatore"]},
                },
            ]
        }
    )
    tutor = await db.members.count_documents({"kind": "tutor"})
    articles_total = await db.articles.count_documents({"status": "published"})
    from datetime import datetime, timezone
    from ..designation_filters import (
        count_refereed_matches_for_season,
        current_season_label,
        published_referee_designations_season_query,
    )

    active_season = current_season_label()
    des_rows = await db.designations.find(
        published_referee_designations_season_query(active_season),
        {
            "_id": 0,
            "matchDate": 1,
            "matchHome": 1,
            "matchAway": 1,
            "matchLabel": 1,
            "role": 1,
        },
    ).to_list(20000)
    matches_this_season = count_refereed_matches_for_season(des_rows, active_season)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    events_upcoming = await db.events.count_documents({"date": {"$gte": today}})
    settings = await db.site_settings.find_one({}, {"_id": 0}) or {}
    founded = settings.get("foundedYear", "1927")
    years = max(1, datetime.now().year - int(founded)) if founded.isdigit() else 99
    return {
        "members": members_total,
        "associati": associati,
        "osservatori": osservatori,
        "tutor": tutor,
        "articles": articles_total,
        "matchesThisSeason": matches_this_season,
        "activeSeason": active_season,
        "eventsUpcoming": events_upcoming,
        "yearsActive": years,
        "foundedYear": founded,
    }


@router.get("/document-sections")
async def list_document_sections():
    from ..document_sections import get_public_document_sections

    db = get_db()
    return await get_public_document_sections(db)


@router.get("/documents")
async def list_documents(category: Optional[str] = None):
    from ..media_urls import resolve_media_url

    db = get_db()
    q = {}
    if category:
        q["category"] = category
    docs = await db.documents.find(q, {"_id": 0}).sort("sortOrder", 1).to_list(500)
    for d in docs:
        if d.get("fileUrl"):
            d["fileUrl"] = resolve_media_url(d["fileUrl"])
    return docs


@router.get("/albums")
async def list_albums():
    db = get_db()
    return await db.albums.find({}, {"_id": 0}).sort("sortOrder", 1).to_list(200)


@router.get("/albums/{slug}")
async def get_album(slug: str):
    db = get_db()
    a = await db.albums.find_one({"slug": slug}, {"_id": 0})
    if not a:
        raise HTTPException(404, "Album non trovato")
    return a


@router.get("/testimonials")
async def list_testimonials():
    db = get_db()
    items = (
        await db.testimonials.find(
            {"$or": [{"status": "published"}, {"status": {"$exists": False}}]},
            {"_id": 0},
        )
        .sort("sortOrder", 1)
        .to_list(100)
    )
    members = await db.members.find(
        {"slug": {"$exists": True, "$ne": ""}},
        {
            "_id": 0,
            "id": 1,
            "slug": 1,
            "firstName": 1,
            "lastName": 1,
            "memberRole": 1,
            "photoUrl": 1,
        },
    ).to_list(2000)
    slug_by_id, member_by_name = build_member_lookups(members, arbitri_only=False)
    member_by_id = {str(m["id"]): m for m in members if m.get("id")}
    for item in items:
        before_slug = (item.get("memberSlug") or "").strip()
        enrich_testimonial(item, slug_by_id, member_by_name, member_by_id)
        resolve_media_fields(item)
        slug_val = (item.get("memberSlug") or "").strip()
        if slug_val and slug_val != before_slug:
            await db.testimonials.update_one(
                {"id": item["id"]}, {"$set": {"memberSlug": slug_val}}
            )
    return items


# ---- Forms ----
# ---- Media / gallery ----
@router.get("/email-logo.png")
async def get_email_logo_png():
    """Logo sezione per email (URL assoluto via PUBLIC_API_URL)."""
    from fastapi.responses import FileResponse

    from ..mailer import _email_logo_file_path, EMAIL_LOGO_FILENAME

    path = _email_logo_file_path()
    if not path:
        raise HTTPException(status_code=404, detail="Logo non disponibile")
    return FileResponse(
        path,
        media_type="image/png",
        filename=EMAIL_LOGO_FILENAME,
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/gallery")
async def get_gallery():
    from ..gallery import list_public_gallery

    db = get_db()
    items = await list_public_gallery(db)
    return [resolve_media_fields(i) for i in items]


@router.get("/instagram/widget")
async def get_instagram_widget(limit: int = 12):
    """Profilo + griglia post per widget home (feed Instagram pubblico)."""
    from ..instagram_widget import build_instagram_widget_payload
    from ..instagram_gallery import parse_instagram_username

    db = get_db()
    settings = (
        await db.site_settings.find_one(
            {"id": "site-settings"},
            {
                "_id": 0,
                "instagramUrl": 1,
                "instagramFollowers": 1,
                "instagramFollowing": 1,
            },
        )
        or {}
    )
    username = parse_instagram_username(settings.get("instagramUrl") or "aia_legnano")

    ig_posts_count = await db.gallery_images.count_documents(
        {"source": "instagram", "status": "approved"}
    )
    stats = {
        "posts": ig_posts_count or None,
        "followers": None,
        "following": None,
    }
    for key, field in (
        ("followers", "instagramFollowers"),
        ("following", "instagramFollowing"),
    ):
        raw = settings.get(field)
        if isinstance(raw, int) and raw >= 0:
            stats[key] = raw
        elif isinstance(raw, str) and raw.strip().isdigit():
            stats[key] = int(raw.strip())

    data = await build_instagram_widget_payload(
        db,
        username,
        limit=max(4, min(limit, 24)),
        stats=stats,
    )
    return data


@router.post("/forms/corso-arbitri", status_code=201)
async def submit_lead(payload: LeadCreate, background: BackgroundTasks):
    db = get_db()
    lead = Lead(**payload.model_dump())
    doc = lead.model_dump()
    await db.leads.insert_one(doc.copy())  # copy to avoid _id mutation
    # email notifications → casella sezione (impostazioni sito / legnano@aia-figc.it)
    notify = await staff_notify_email(db)
    if notify:
        background.add_task(
            send_email,
            notify,
            f"Nuova candidatura corso arbitri – "
            f"{format_person_name(lead.firstName, lead.lastName)}",
            render_lead_email(doc),
        )
    # confirmation to user
    background.add_task(
        send_email,
        lead.email,
        "Grazie! Abbiamo ricevuto la tua candidatura - AIA Legnano",
        render_lead_confirmation_email(
            first_name=lead.firstName,
            contact_preference=lead.contactPreference,
        ),
    )
    return {"ok": True, "id": lead.id}


@router.post("/forms/contatti", status_code=201)
async def submit_contact(payload: ContactCreate, background: BackgroundTasks):
    db = get_db()
    msg = ContactMessage(**payload.model_dump())
    doc = msg.model_dump()
    await db.contact_messages.insert_one(doc.copy())
    notify = await staff_notify_email(db)
    if notify:
        background.add_task(
            send_email,
            notify,
            f"[Sito AIA Legnano] {payload.subject or 'Nuovo messaggio'}",
            render_contact_email(doc),
        )
    return {"ok": True, "id": msg.id}
