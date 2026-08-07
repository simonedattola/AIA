"""Area riservata associati — API su MongoDB (stesso backend del sito)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel, Field

from ..db import get_db
from ..security import (
    create_token,
    verify_password,
    hash_password,
    require_member,
    require_admin,
)
from ..uploads import (
    save_upload,
    IMAGE_EXTENSIONS,
    DEFAULT_IMAGE_MAX_BYTES,
    DEFAULT_MESSAGE_ATTACHMENT_MAX_BYTES,
)
from ..rate_limit import client_ip, enforce_rate_limit
from ..models import (
    PortalLoginRequest,
    PresenzaEventoUpdate,
    MessaggioInternoCreate,
    MessaggioModificaBody,
    MessaggioReazioneBody,
    PreferitoCreate,
    ComunicazioneInternaCreate,
    ComunicazioneRispostaCreate,
    GruppoChatCreate,
    GruppoChatUpdate,
)
from ..portal_messaging import (
    list_conversations,
    get_conversation,
    send_message,
    create_group,
    chat_id_for_group,
    get_contact_info,
    get_group_info,
    update_group,
    leave_group,
    delete_conversation_for_member,
    edit_message,
    delete_message,
    toggle_reaction,
    parse_chat_id,
)
from ..designation_level import highest_championship_label
from ..portal_password import member_can_use_portal, default_portal_password
from ..portal_member import member_public, is_staff_portal
from ..media_urls import resolve_media_fields, resolve_attachments
from ..paths import UPLOAD_DIR
from ..member_roles import MEMBER_ROLES, normalize_member
from ..comunicazioni_helpers import (
    comunicazione_destinatari,
    comunicazione_letture_map,
    comunicazione_letture_report,
)
from ..designation_filters import (
    current_season_label,
    season_label_from_iso,
    match_date_in_season_clause,
    distinct_seasons_from_dates,
    parse_season,
    event_date_in_season_clause,
    iso_datetime_in_season_clause,
    merge_mongo_queries,
)

router = APIRouter(prefix="/api/portal", tags=["portal"])

PRESENZA_STATI = {"PRESENTE", "ASSENTE", "IN_DUBBIO", "NON_RISPOSTO"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _get_member(db, member_id: str) -> dict:
    m = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not m:
        raise HTTPException(status_code=404, detail="Associato non trovato")
    return m


async def _presenza_map(db, event_id: str) -> dict[str, str]:
    rows = await db.presenze_evento.find({"eventId": event_id}, {"_id": 0}).to_list(5000)
    return {r["memberId"]: r.get("stato", "NON_RISPOSTO") for r in rows}


def _event_date_in_season_clause(season: str) -> dict | None:
    return event_date_in_season_clause(season)


async def _member_season_presenze_stats(db, member_id: str, season: str | None = None) -> dict:
    """Presenze/assenze dell'associato nella stagione calcistica (1 ago – 31 lug)."""
    label = season or current_season_label()
    clause = _event_date_in_season_clause(label)
    if not clause:
        return {"stagione": label, "presenti": 0, "assenti": 0}
    events = await db.events.find(clause, {"_id": 0, "id": 1}).to_list(5000)
    event_ids = [e["id"] for e in events]
    if not event_ids:
        return {"stagione": label, "presenti": 0, "assenti": 0}
    rows = await db.presenze_evento.find(
        {"memberId": member_id, "eventId": {"$in": event_ids}},
        {"_id": 0, "stato": 1},
    ).to_list(5000)
    presenti = sum(1 for r in rows if r.get("stato") == "PRESENTE")
    assenti = sum(1 for r in rows if r.get("stato") == "ASSENTE")
    return {"stagione": label, "presenti": presenti, "assenti": assenti}


def _normalize_presenza_stato(stato: str | None) -> str:
    return (stato or "NON_RISPOSTO").upper()


def _presenza_locked(stato: str) -> bool:
    return _normalize_presenza_stato(stato) in ("PRESENTE", "ASSENTE")


async def _upsert_presenza(db, event_id: str, member_id: str, stato: str, updated_by: str) -> None:
    existing = await db.presenze_evento.find_one(
        {"eventId": event_id, "memberId": member_id},
        {"_id": 0, "id": 1},
    )
    doc = {
        "eventId": event_id,
        "memberId": member_id,
        "stato": stato,
        "updatedAt": _now(),
        "updatedBy": updated_by,
    }
    if existing:
        doc["id"] = existing["id"]
    else:
        doc["id"] = str(uuid.uuid4())
    await db.presenze_evento.update_one(
        {"eventId": event_id, "memberId": member_id},
        {"$set": doc},
        upsert=True,
    )


# ---- Auth associato ----
@router.post("/login")
async def portal_login(payload: PortalLoginRequest, request: Request):
    enforce_rate_limit(
        f"portal-login:{client_ip(request)}",
        max_hits=15,
        window_seconds=300,
        detail="Troppi tentativi di login, riprova tra poco",
    )
    db = get_db()
    codice = (payload.codice or "").strip()
    if not codice:
        raise HTTPException(status_code=400, detail="Codice meccanografico obbligatorio")
    member = await db.members.find_one({"meccanografico": codice}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    if not member_can_use_portal(member):
        raise HTTPException(status_code=403, detail="Accesso portale non abilitato per questo profilo")
    if not member.get("passwordHash"):
        from ..portal_credentials import ensure_member_portal_credentials
        await ensure_member_portal_credentials(member)
        member = await db.members.find_one({"id": member["id"]}, {"_id": 0})
    if not verify_password(payload.password, member.get("passwordHash", "")):
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    token = create_token({
        "sub": member["id"],
        "role": "member",
        "memberId": member["id"],
        "staffPortal": is_staff_portal(member),
        "name": f"{member.get('firstName', '')} {member.get('lastName', '')}".strip(),
    })
    resolve_media_fields(member)
    return {"token": token, "member": member_public(member)}


@router.get("/me")
async def portal_me(auth=Depends(require_member)):
    db = get_db()
    m = await _get_member(db, auth["memberId"])
    resolve_media_fields(m)
    return member_public(m)


class ProfileUpdate(BaseModel):
    bio: str = ""
    emailVisibile: bool = False
    telefonoVisibile: bool = False
    emailNotifyEvents: bool = False
    emailNotifyEventLeadHours: int = 24
    emailNotifyComunicazioni: bool = False
    emailNotifyMessages: bool = False
    photoUrl: str = ""
    password: str = ""
    newPassword: str = ""


class TestimonialSubmit(BaseModel):
    quote: str
    role: str = ""


@router.put("/me")
async def portal_update_me(payload: ProfileUpdate, auth=Depends(require_member)):
    db = get_db()
    m = await _get_member(db, auth["memberId"])
    lead = payload.emailNotifyEventLeadHours
    if lead not in (24, 12, 6, 1):
        lead = 24
    if payload.emailNotifyEvents and not (m.get("email") or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Per ricevere notifiche sugli eventi serve un indirizzo email in anagrafica. Contatta la sezione.",
        )
    if (payload.emailNotifyComunicazioni or payload.emailNotifyMessages) and not (m.get("email") or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Per ricevere notifiche email serve un indirizzo email in anagrafica. Contatta la sezione.",
        )
    upd = {
        "bio": (payload.bio or "").strip(),
        "emailVisibile": payload.emailVisibile,
        "telefonoVisibile": payload.telefonoVisibile,
        "emailNotifyEvents": payload.emailNotifyEvents,
        "emailNotifyEventLeadHours": lead,
        "emailNotifyComunicazioni": payload.emailNotifyComunicazioni,
        "emailNotifyMessages": payload.emailNotifyMessages,
        "updatedAt": _now(),
    }
    if payload.photoUrl:
        upd["photoUrl"] = payload.photoUrl.strip()
    if payload.newPassword:
        if not payload.password or not verify_password(payload.password, m.get("passwordHash", "")):
            raise HTTPException(status_code=400, detail="Password attuale non corretta")
        if len(payload.newPassword) < 6:
            raise HTTPException(status_code=400, detail="Nuova password troppo corta")
        upd["passwordHash"] = hash_password(payload.newPassword)
    await db.members.update_one({"id": m["id"]}, {"$set": upd})
    m.update(upd)
    resolve_media_fields(m)
    return member_public(m)


# ---- Dashboard ----
async def _portal_events_for_member(
    db,
    mid: str,
    *,
    from_date: str | None = None,
    current_season: bool = False,
    limit: int | None = None,
) -> list[dict]:
    from ..event_access import member_invited_to_event

    parts: list[dict | None] = []
    if current_season:
        parts.append(event_date_in_season_clause())
    if from_date:
        parts.append({"date": {"$gte": from_date}})
    q = merge_mongo_queries(*parts)
    cursor = db.events.find(q, {"_id": 0}).sort("date", 1)
    if limit:
        cursor = cursor.limit(limit * 3)
    events = await cursor.to_list(limit * 3 if limit else 500)
    return [ev for ev in events if member_invited_to_event(ev, mid)][: limit or len(events)]


@router.get("/dashboard")
async def portal_dashboard(auth=Depends(require_member)):
    db = get_db()
    mid = auth["memberId"]
    m = await db.members.find_one({"id": mid}, {"_id": 0})
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    events = await _portal_events_for_member(db, mid, from_date=today, current_season=True, limit=1)
    pres_map = {}
    for ev in events:
        pres_map[ev["id"]] = (await _presenza_map(db, ev["id"])).get(mid, "NON_RISPOSTO")
    next_designation = None
    if m:
        from ..designation_queries import find_next_member_designation
        from ..member_roles import normalize_member

        normalize_member(m)
        next_designation = await find_next_member_designation(db, m)
    comm_q = merge_mongo_queries(
        {"$or": [{"allMembers": True}, {"memberIds": mid}]},
        iso_datetime_in_season_clause("createdAt"),
    )
    all_comm = await db.comunicazioni_interne.find(comm_q, {"_id": 0, "id": 1}).to_list(500)
    comm_ids = [c["id"] for c in all_comm]
    read_ids = set()
    if comm_ids:
        reads = await db.comunicazioni_letture.find(
            {"memberId": mid, "comunicazioneId": {"$in": comm_ids}, "letta": True},
            {"_id": 0, "comunicazioneId": 1},
        ).to_list(500)
        read_ids = {r["comunicazioneId"] for r in reads}
    comm_unread = len(comm_ids) - len(read_ids)
    latest = await db.comunicazioni_interne.find(
        comm_q,
        {"_id": 0, "id": 1, "title": 1, "createdAt": 1},
    ).sort("createdAt", -1).limit(2).to_list(2)
    for c in latest:
        c["letta"] = c["id"] in read_ids
    from ..portal_messaging import count_unread_messages

    messaggi_non_letti = await count_unread_messages(db, mid)
    return {
        "upcomingEvents": [
            {
                **e,
                "mioStato": (stato := pres_map.get(e["id"], "NON_RISPOSTO")),
                "presenzaLocked": _presenza_locked(stato),
                "attachments": resolve_attachments(e.get("attachments")),
            }
            for e in events
        ],
        "nextDesignation": next_designation,
        "comunicazioniNonLette": max(0, comm_unread),
        "messaggiNonLetti": messaggi_non_letti,
        "latestComunicazioni": latest,
    }


# ---- Calendario & presenze (self-service) ----
@router.get("/calendario")
async def portal_calendario(auth=Depends(require_member)):
    db = get_db()
    mid = auth["memberId"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    events = await _portal_events_for_member(db, mid, from_date=today, current_season=True)
    out = []
    for ev in events:
        stato = (await _presenza_map(db, ev["id"])).get(mid, "NON_RISPOSTO")
        out.append({
            **ev,
            "mioStato": stato,
            "presenzaLocked": _presenza_locked(stato),
            "attachments": resolve_attachments(ev.get("attachments")),
        })
    stats = await _member_season_presenze_stats(db, mid)
    return {"eventi": out, **stats}


class SelfPresenzaBody(BaseModel):
    stato: str


@router.put("/calendario/{event_id}/presenza")
async def portal_set_presenza(event_id: str, body: SelfPresenzaBody, auth=Depends(require_member)):
    stato = (body.stato or "").upper()
    if stato not in ("PRESENTE", "ASSENTE", "IN_DUBBIO"):
        raise HTTPException(status_code=400, detail="Stato non valido")
    db = get_db()
    ev = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not ev:
        raise HTTPException(status_code=404, detail="Evento non trovato")
    mid = auth["memberId"]
    from ..event_access import member_invited_to_event

    if not member_invited_to_event(ev, mid):
        raise HTTPException(status_code=403, detail="Non sei invitato a questo evento")
    existing = await db.presenze_evento.find_one(
        {"eventId": event_id, "memberId": mid},
        {"_id": 0, "stato": 1},
    )
    existing_stato = _normalize_presenza_stato(existing.get("stato") if existing else None)
    if existing_stato in ("PRESENTE", "ASSENTE"):
        raise HTTPException(status_code=409, detail="Presenza già confermata e non modificabile")
    if existing_stato == "IN_DUBBIO" and stato not in ("PRESENTE", "ASSENTE"):
        raise HTTPException(status_code=400, detail="Conferma presente o assente")
    await _upsert_presenza(db, event_id, mid, stato, "member")
    return {"ok": True, "stato": stato, "presenzaLocked": _presenza_locked(stato)}


# ---- Storico arbitrale ----
@router.get("/storico")
async def portal_storico(season: Optional[str] = None, auth=Depends(require_member)):
    db = get_db()
    mid = auth["memberId"]
    m = await _get_member(db, mid)
    q: dict = {"memberId": mid}
    if not mid:
        q = {"memberName": f"{m.get('firstName', '')} {m.get('lastName', '')}".strip()}
    all_items = await db.designations.find(q, {"_id": 0}).sort("matchDate", -1).to_list(1000)
    from ..designation_enrich import enrich_designation, build_member_lookups
    from ..member_roles import legacy_arbitri_query

    members = await db.members.find(legacy_arbitri_query(), {"_id": 0}).to_list(2000)
    slug_by_id, member_by_name = build_member_lookups(members)
    for item in all_items:
        enrich_designation(item, slug_by_id, member_by_name)

    dates = [i.get("matchDate", "") for i in all_items]
    seasons = distinct_seasons_from_dates(dates)
    active = season or (seasons[0] if seasons else current_season_label())
    season_clause = match_date_in_season_clause(active)
    items = all_items
    if season_clause:
        start, end = season_clause["matchDate"]["$gte"], season_clause["matchDate"]["$lte"]
        items = [i for i in all_items if start <= (i.get("matchDate") or "") <= end]

    categoria_massima = highest_championship_label(items)

    return {
        "stats": {
            "stagione": active,
            "categoriaMassima": categoria_massima,
            "totaleDesignazioni": len(items),
        },
        "seasonsAvailable": seasons,
        "activeSeason": active,
        "designations": items,
    }


# ---- Utility (materiale eventi, polo, link utili) ----
@router.get("/utility")
async def portal_utility(auth=Depends(require_member)):
    from ..media_urls import resolve_media_url, resolve_attachments
    from ..event_access import member_invited_to_event

    db = get_db()
    mid = auth["memberId"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    settings = await db.site_settings.find_one({"id": "site-settings"}, {"_id": 0, "utilityPolo": 1})
    polo = (settings or {}).get("utilityPolo") or {"bodyHtml": ""}
    polo = {"bodyHtml": polo.get("bodyHtml") or ""}

    events = await db.events.find(
        merge_mongo_queries(
            {"utilityMaterial.0": {"$exists": True}},
            event_date_in_season_clause(),
            {"date": {"$gte": today}},
        ),
        {"_id": 0},
    ).sort("date", 1).to_list(500)

    event_material = []
    for ev in events:
        if not member_invited_to_event(ev, mid):
            continue
        material = resolve_attachments(ev.get("utilityMaterial"))
        if not material:
            continue
        event_material.append({
            "id": ev["id"],
            "date": ev.get("date", ""),
            "orario": ev.get("orario", ""),
            "tipo": ev.get("tipo", ""),
            "titolo": ev.get("titolo", ""),
            "descrizione": ev.get("descrizione", ""),
            "utilityMaterial": material,
        })

    links = []
    items = await db.utility_items.find({"section": "link_utili"}, {"_id": 0}).sort("sortOrder", 1).to_list(500)
    for item in items:
        row = {**item}
        if row.get("fileUrl"):
            row["fileUrl"] = resolve_media_url(row["fileUrl"])
        if row.get("url") and not row["url"].startswith(("http://", "https://", "/")):
            row["url"] = resolve_media_url(row["url"])
        links.append(row)

    return {
        "polo": polo,
        "event_material": event_material,
        "link_utili": links,
        "stagione": current_season_label(),
    }


# ---- Area tecnica (documenti reali) ----
@router.get("/documenti")
async def portal_documenti(category: Optional[str] = None, auth=Depends(require_member)):
    db = get_db()
    q = {}
    if category:
        q["category"] = category
    from ..media_urls import resolve_media_url

    docs = await db.documents.find(q, {"_id": 0}).sort("sortOrder", 1).to_list(500)
    mid = auth["memberId"]
    favs = await db.preferiti.find({"memberId": mid, "tipo": "DOCUMENTO"}, {"_id": 0}).to_list(500)
    fav_ids = {f["elementoId"] for f in favs}
    for d in docs:
        d["preferito"] = d["id"] in fav_ids
        if d.get("fileUrl"):
            d["fileUrl"] = resolve_media_url(d["fileUrl"])
    return docs


# ---- Comunicazioni interne ----
async def _comunicazione_visible_to(db, comm: dict, member_id: str) -> bool:
    if comm.get("allMembers"):
        return True
    return member_id in (comm.get("memberIds") or [])


async def _comunicazione_letta(db, comm_id: str, member_id: str) -> bool:
    row = await db.comunicazioni_letture.find_one(
        {"comunicazioneId": comm_id, "memberId": member_id},
        {"_id": 0, "letta": 1},
    )
    return bool(row and row.get("letta"))


@router.get("/comunicazioni")
async def portal_comunicazioni(auth=Depends(require_member)):
    db = get_db()
    mid = auth["memberId"]
    q = merge_mongo_queries(
        {"$or": [{"allMembers": True}, {"memberIds": mid}]},
        iso_datetime_in_season_clause("createdAt"),
    )
    items = await db.comunicazioni_interne.find(q, {"_id": 0}).sort("createdAt", -1).to_list(200)
    out = []
    for c in items:
        letta = await _comunicazione_letta(db, c["id"], mid)
        risposte = c.get("risposte") or []
        mie = [r for r in risposte if r.get("memberId") == mid]
        out.append({
            **c,
            "letta": letta,
            "risposte": risposte,
            "mieRisposte": mie,
            "risposteCount": len(risposte),
            "attachments": resolve_attachments(c.get("attachments")),
        })
    return out


@router.get("/comunicazioni/{comm_id}")
async def portal_comunicazione_detail(comm_id: str, auth=Depends(require_member)):
    db = get_db()
    mid = auth["memberId"]
    c = await db.comunicazioni_interne.find_one({"id": comm_id}, {"_id": 0})
    if not c or not await _comunicazione_visible_to(db, c, mid):
        raise HTTPException(status_code=404, detail="Comunicazione non trovata")
    read_row = await db.comunicazioni_letture.find_one(
        {"comunicazioneId": comm_id, "memberId": mid},
        {"_id": 0, "letta": 1, "readAt": 1},
    )
    if read_row and read_row.get("letta"):
        read_at = read_row.get("readAt")
    else:
        read_at = _now()
        await db.comunicazioni_letture.update_one(
            {"comunicazioneId": comm_id, "memberId": mid},
            {"$set": {"letta": True, "readAt": read_at, "comunicazioneId": comm_id, "memberId": mid}},
            upsert=True,
        )
    return {
        **c,
        "letta": True,
        "readAt": read_at,
        "risposte": c.get("risposte") or [],
        "attachments": resolve_attachments(c.get("attachments")),
    }


@router.put("/comunicazioni/{comm_id}/letta")
async def portal_comunicazione_letta(comm_id: str, auth=Depends(require_member)):
    db = get_db()
    mid = auth["memberId"]
    c = await db.comunicazioni_interne.find_one({"id": comm_id}, {"_id": 0, "id": 1})
    if not c or not await _comunicazione_visible_to(db, c, mid):
        raise HTTPException(status_code=404, detail="Comunicazione non trovata")
    read_at = _now()
    await db.comunicazioni_letture.update_one(
        {"comunicazioneId": comm_id, "memberId": mid},
        {"$set": {"letta": True, "readAt": read_at, "comunicazioneId": comm_id, "memberId": mid}},
        upsert=True,
    )
    return {"ok": True, "readAt": read_at}


@router.post("/comunicazioni/{comm_id}/risposte")
async def portal_comunicazione_risposta(
    comm_id: str, payload: ComunicazioneRispostaCreate, auth=Depends(require_member)
):
    testo = (payload.testo or "").strip()
    if len(testo) < 2:
        raise HTTPException(status_code=400, detail="Risposta troppo corta")
    db = get_db()
    mid = auth["memberId"]
    c = await db.comunicazioni_interne.find_one({"id": comm_id}, {"_id": 0})
    if not c or not await _comunicazione_visible_to(db, c, mid):
        raise HTTPException(status_code=404, detail="Comunicazione non trovata")
    if c.get("allowReplies") is False:
        raise HTTPException(status_code=403, detail="Risposte non consentite")
    m = await _get_member(db, mid)
    risposta = {
        "id": str(uuid.uuid4()),
        "memberId": mid,
        "memberName": f"{m.get('firstName', '')} {m.get('lastName', '')}".strip(),
        "testo": testo,
        "createdAt": _now(),
    }
    await db.comunicazioni_interne.update_one(
        {"id": comm_id},
        {"$push": {"risposte": risposta}},
    )
    return risposta


@router.get("/news")
async def portal_news(auth=Depends(require_member)):
    return await portal_comunicazioni(auth)


# ---- Premi ----
@router.get("/premi")
async def portal_premi(auth=Depends(require_member)):
    db = get_db()
    mid = auth["memberId"]
    m = await _get_member(db, mid)
    menzioni = await db.articles.find(
        {
            "status": "published",
            "relatedMemberIds": mid,
            "portalOnly": {"$ne": True},
        },
        {"_id": 0, "title": 1, "excerpt": 1, "publishedAt": 1, "category": 1, "slug": 1},
    ).sort("publishedAt", -1).to_list(50)
    return {"awards": m.get("awards") or [], "menzioni": menzioni, "member": member_public(m)}


# ---- Media (foto carosello con tag associato) ----
@router.get("/media")
async def portal_media(auth=Depends(require_member)):
    from ..media_urls import resolve_media_fields

    db = get_db()
    mid = auth["memberId"]
    items = await db.gallery_images.find(
        {"status": "approved", "memberIds": mid},
        {"_id": 0},
    ).sort([("sortOrder", 1), ("photoDate", -1), ("createdAt", -1)]).to_list(500)
    for item in items:
        resolve_media_fields(item, fields=("url", "path", "sourceUrl"))
    return items


# ---- Messaggi interni (chat dirette + gruppi) ----
@router.get("/messaggi/conversazioni")
async def portal_conversazioni(auth=Depends(require_member)):
    return await list_conversations(get_db(), auth["memberId"])


@router.get("/messaggi/conversazioni/{chat_id}")
async def portal_conversazione(chat_id: str, auth=Depends(require_member)):
    return await get_conversation(get_db(), chat_id, auth["memberId"], _now())


@router.delete("/messaggi/conversazioni/{chat_id}")
async def portal_elimina_conversazione(chat_id: str, auth=Depends(require_member)):
    return await delete_conversation_for_member(get_db(), chat_id, auth["memberId"], _now())


@router.get("/messaggi/conversazioni/{chat_id}/contatto")
async def portal_contatto_chat(chat_id: str, auth=Depends(require_member)):
    kind, target_id = parse_chat_id(chat_id)
    if kind != "direct":
        raise HTTPException(status_code=400, detail="Disponibile solo per chat private")
    return await get_contact_info(get_db(), target_id, auth["memberId"])


@router.get("/messaggi/conversazioni/{chat_id}/gruppo")
async def portal_info_gruppo(chat_id: str, auth=Depends(require_member)):
    return await get_group_info(get_db(), chat_id, auth["memberId"])


@router.post("/messaggi/conversazioni/{chat_id}")
async def portal_invia_in_conversazione(
    chat_id: str, payload: MessaggioInternoCreate, auth=Depends(require_member)
):
    return await send_message(
        get_db(), chat_id, auth["memberId"], payload.model_dump(), _now(), _get_member
    )


@router.post("/messaggi/allegati")
async def portal_upload_allegato(file: UploadFile = File(...), auth=Depends(require_member)):
    allowed = {
        ".jpg", ".jpeg", ".png", ".webp", ".gif",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".zip",
    }
    from pathlib import Path as _Path

    ext = _Path(file.filename or "").suffix.lower() or ".bin"
    _target, name, _size = await save_upload(
        file,
        allowed_ext=allowed,
        max_bytes=DEFAULT_MESSAGE_ATTACHMENT_MAX_BYTES,
        name_prefix="msg_",
    )
    from ..media_urls import resolve_media_url

    rel_path = f"/api/uploads/{name}"
    mime = file.content_type or ""
    tipo = "image" if mime.startswith("image/") or ext in IMAGE_EXTENSIONS else "file"
    return {
        "attachmentUrl": rel_path,
        "attachmentUrlResolved": resolve_media_url(rel_path),
        "attachmentName": file.filename or name,
        "attachmentMime": mime,
        "tipo": tipo,
    }


@router.put("/messaggi/{msg_id}")
async def portal_modifica_messaggio(
    msg_id: str, payload: MessaggioModificaBody, auth=Depends(require_member)
):
    return await edit_message(get_db(), msg_id, auth["memberId"], payload.testo, _now())


@router.delete("/messaggi/{msg_id}")
async def portal_elimina_messaggio(msg_id: str, auth=Depends(require_member)):
    return await delete_message(get_db(), msg_id, auth["memberId"], _now())


@router.post("/messaggi/{msg_id}/reazioni")
async def portal_reazione_messaggio(
    msg_id: str, payload: MessaggioReazioneBody, auth=Depends(require_member)
):
    return await toggle_reaction(
        get_db(), msg_id, auth["memberId"], payload.emoji, _now(), _get_member
    )


@router.post("/messaggi/gruppi")
async def portal_crea_gruppo(payload: GruppoChatCreate, auth=Depends(require_member)):
    g = await create_group(
        get_db(),
        auth["memberId"],
        payload.name,
        payload.memberIds or [],
        _now(),
        photo_url=payload.photoUrl or "",
        description=payload.description or "",
    )
    return {**g, "chatId": chat_id_for_group(g["id"])}


@router.put("/messaggi/gruppi/{gruppo_id}")
async def portal_aggiorna_gruppo(
    gruppo_id: str, payload: GruppoChatUpdate, auth=Depends(require_member)
):
    data = payload.model_dump(exclude_unset=True)
    return await update_group(get_db(), gruppo_id, auth["memberId"], data, _now())


@router.post("/messaggi/gruppi/{gruppo_id}/esci")
async def portal_esci_gruppo(gruppo_id: str, auth=Depends(require_member)):
    return await leave_group(get_db(), gruppo_id, auth["memberId"], _now())


@router.get("/messaggi")
async def portal_messaggi(auth=Depends(require_member)):
    return await portal_conversazioni(auth)


@router.get("/messaggi/associati")
async def portal_lista_associati(auth=Depends(require_member)):
    """Profili associati per nuove chat e gruppi (solo tra associati)."""
    db = get_db()
    items = await db.members.find(
        {"memberRole": {"$in": list(MEMBER_ROLES)}, "slug": {"$exists": True, "$ne": ""}},
        {"_id": 0, "id": 1, "firstName": 1, "lastName": 1, "memberRole": 1, "photoUrl": 1, "observerType": 1},
    ).sort([("lastName", 1), ("firstName", 1)]).to_list(500)
    for it in items:
        normalize_member(it)
        resolve_media_fields(it)
    from ..member_roles import member_role_label

    return [
        {
            "id": i["id"],
            "firstName": i.get("firstName"),
            "lastName": i.get("lastName"),
            "photoUrl": i.get("photoUrl"),
            "roleLabel": member_role_label(i.get("memberRole"), i.get("observerType")),
        }
        for i in items
        if i["id"] != auth["memberId"]
    ]


@router.get("/gallery/mine")
async def portal_gallery_mine(auth=Depends(require_member)):
    db = get_db()
    return await (
        db.gallery_images.find({"memberId": auth["memberId"]}, {"_id": 0})
        .sort("createdAt", -1)
        .to_list(200)
    )


@router.get("/gallery/categories")
async def portal_gallery_categories(auth=Depends(require_member)):
    from ..article_categories import get_public_article_categories

    db = get_db()
    return await get_public_article_categories(db)


@router.post("/gallery/upload")
async def portal_gallery_upload(
    file: UploadFile = File(...),
    caption: str = Form(""),
    category: str = Form(""),
    auth=Depends(require_member),
):
    _target, name, _size = await save_upload(
        file,
        allowed_ext=IMAGE_EXTENSIONS,
        max_bytes=DEFAULT_IMAGE_MAX_BYTES,
    )
    from ..article_categories import validate_member_category_choice
    from ..media_urls import resolve_media_url
    from ..gallery import save_uploaded_gallery_image

    db = get_db()
    try:
        category_resolved = await validate_member_category_choice(db, category)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    m = await _get_member(db, auth["memberId"])
    rel_path = f"/api/uploads/{name}"
    url = resolve_media_url(rel_path)
    member_name = f"{m.get('firstName', '')} {m.get('lastName', '')}".strip()
    doc = await save_uploaded_gallery_image(
        db,
        url=url,
        path=rel_path,
        caption=caption.strip(),
        status="pending",
        source="member",
        member_id=auth["memberId"],
        member_name=member_name,
        category=category_resolved,
    )
    return doc


@router.post("/upload-foto")
async def portal_upload_foto(file: UploadFile = File(...), auth=Depends(require_member)):
    _target, name, _size = await save_upload(
        file,
        allowed_ext=IMAGE_EXTENSIONS,
        max_bytes=DEFAULT_IMAGE_MAX_BYTES,
    )
    from ..media_urls import resolve_media_url

    rel_path = f"/api/uploads/{name}"
    url = resolve_media_url(rel_path)
    db = get_db()
    await db.members.update_one(
        {"id": auth["memberId"]},
        {"$set": {"photoUrl": rel_path, "updatedAt": _now()}},
    )
    return {"url": url, "photoUrl": rel_path}


@router.delete("/upload-foto")
async def portal_delete_foto(auth=Depends(require_member)):
    db = get_db()
    m = await _get_member(db, auth["memberId"])
    old = (m.get("photoUrl") or "").strip()
    await db.members.update_one(
        {"id": auth["memberId"]},
        {"$set": {"photoUrl": "", "updatedAt": _now()}},
    )
    from ..media_urls import upload_basename

    name = upload_basename(old)
    if name:
        (UPLOAD_DIR / name).unlink(missing_ok=True)
    return {"ok": True, "photoUrl": ""}


@router.post("/testimonianza")
async def portal_submit_testimonial(payload: TestimonialSubmit, auth=Depends(require_member)):
    quote = (payload.quote or "").strip()
    if len(quote) < 20:
        raise HTTPException(status_code=400, detail="Testimonianza troppo corta")
    db = get_db()
    m = await _get_member(db, auth["memberId"])
    from ..models import Testimonial

    t = Testimonial(
        name=f"{m.get('firstName', '')} {m.get('lastName', '')}".strip(),
        role=(payload.role or m.get("category") or "Associato").strip(),
        quote=quote,
        photoUrl=m.get("photoUrl") or "",
        memberId=m["id"],
        memberSlug=m.get("slug") or "",
        status="pending",
    )
    doc = t.model_dump()
    await db.testimonials.insert_one(doc.copy())
    return {"ok": True, "status": "pending", "message": "Inviata per approvazione"}


# ---- Preferiti ----
@router.get("/preferiti")
async def portal_preferiti(auth=Depends(require_member)):
    db = get_db()
    return await db.preferiti.find({"memberId": auth["memberId"]}, {"_id": 0}).to_list(500)


@router.post("/preferiti")
async def portal_add_preferito(payload: PreferitoCreate, auth=Depends(require_member)):
    db = get_db()
    doc = {
        "id": str(uuid.uuid4()),
        "memberId": auth["memberId"],
        "tipo": payload.tipo,
        "elementoId": payload.elementoId,
        "createdAt": _now(),
    }
    existing = await db.preferiti.find_one(
        {"memberId": auth["memberId"], "tipo": payload.tipo, "elementoId": payload.elementoId},
        {"_id": 0},
    )
    if existing:
        return existing
    await db.preferiti.insert_one(doc.copy())
    return doc


@router.delete("/preferiti/{pref_id}")
async def portal_del_preferito(pref_id: str, auth=Depends(require_member)):
    db = get_db()
    await db.preferiti.delete_one({"id": pref_id, "memberId": auth["memberId"]})
    return {"ok": True}


# ========== Admin portale (JWT admin) ==========
@router.get("/admin/presenze/associati/{member_id}")
async def admin_presenze_associato(member_id: str, admin=Depends(require_admin)):
    db = get_db()
    from ..event_access import member_invited_to_event

    m = await db.members.find_one({"id": member_id}, {"_id": 0, "id": 1, "firstName": 1, "lastName": 1})
    if not m:
        raise HTTPException(status_code=404, detail="Associato non trovato")
    events = await db.events.find({}, {"_id": 0, "id": 1, "titolo": 1, "date": 1, "invitedMemberIds": 1, "relatedMemberIds": 1}).sort("date", -1).to_list(500)
    events = [ev for ev in events if member_invited_to_event(ev, member_id)]
    pres_rows = await db.presenze_evento.find({"memberId": member_id}, {"_id": 0, "eventId": 1, "stato": 1}).to_list(5000)
    pres_by_event = {p["eventId"]: p.get("stato", "NON_RISPOSTO") for p in pres_rows}
    eventi = [
        {
            "eventId": ev["id"],
            "titolo": ev.get("titolo") or "",
            "date": ev.get("date") or "",
            "stato": pres_by_event.get(ev["id"], "NON_RISPOSTO"),
        }
        for ev in events
    ]
    stats = await _member_season_presenze_stats(db, member_id)
    return {"member": m, "eventi": eventi, "stats": stats}


@router.get("/admin/presenze/eventi/{event_id}")
async def admin_presenze_evento_detail(event_id: str, admin=Depends(require_admin)):
    db = get_db()
    ev = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not ev:
        raise HTTPException(status_code=404, detail="Evento non trovato")
    from ..event_access import event_invited_member_ids
    from ..member_roles import normalize_member

    invited_ids = event_invited_member_ids(ev)
    member_q = {"memberRole": {"$in": list(MEMBER_ROLES)}, "slug": {"$exists": True, "$ne": ""}}
    if invited_ids:
        member_q["id"] = {"$in": invited_ids}
    members = await db.members.find(member_q, {"_id": 0}).sort([("lastName", 1), ("firstName", 1)]).to_list(500)
    pres_map = await _presenza_map(db, event_id)
    rows = []
    for m in members:
        normalize_member(m)
        rows.append({
            "memberId": m["id"],
            "nome": f"{m.get('firstName', '')} {m.get('lastName', '')}".strip(),
            "meccanografico": m.get("meccanografico", ""),
            "categoria": m.get("category", ""),
            "stato": pres_map.get(m["id"], "NON_RISPOSTO"),
        })
    return {"event": ev, "associati": rows}


@router.put("/admin/presenze/eventi/{event_id}")
async def admin_presenze_evento_update(event_id: str, updates: List[PresenzaEventoUpdate], admin=Depends(require_admin)):
    db = get_db()
    ev = await db.events.find_one({"id": event_id}, {"_id": 0, "id": 1})
    if not ev:
        raise HTTPException(status_code=404, detail="Evento non trovato")
    for u in updates:
        stato = (u.stato or "NON_RISPOSTO").upper()
        if stato not in PRESENZA_STATI:
            raise HTTPException(status_code=400, detail=f"Stato invalido: {stato}")
        await _upsert_presenza(db, event_id, u.memberId, stato, "admin")
    return {"ok": True}


@router.get("/admin/comunicazioni")
async def admin_list_comunicazioni(admin=Depends(require_admin)):
    db = get_db()
    q = iso_datetime_in_season_clause("createdAt") or {}
    items = await db.comunicazioni_interne.find(q, {"_id": 0}).sort("createdAt", -1).to_list(200)
    for c in items:
        destinatari = await comunicazione_destinatari(db, c)
        dest_ids = [m["id"] for m in destinatari]
        letture = await comunicazione_letture_map(db, c["id"], dest_ids)
        c["destinatariCount"] = len(destinatari)
        c["letteCount"] = len(letture)
        c["risposteCount"] = len(c.get("risposte") or [])
    return items


@router.get("/admin/comunicazioni/{comm_id}/letture")
async def admin_comunicazione_letture(comm_id: str, admin=Depends(require_admin)):
    db = get_db()
    c = await db.comunicazioni_interne.find_one({"id": comm_id}, {"_id": 0})
    if not c:
        raise HTTPException(status_code=404, detail="Comunicazione non trovata")
    return await comunicazione_letture_report(db, c)


@router.post("/admin/comunicazioni")
async def admin_crea_comunicazione(payload: ComunicazioneInternaCreate, admin=Depends(require_admin)):
    db = get_db()
    title = (payload.title or "").strip()
    body = (payload.bodyHtml or payload.testo or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Titolo obbligatorio")
    if not body:
        raise HTTPException(status_code=400, detail="Testo obbligatorio")
    member_ids = list(payload.memberIds or [])
    if not payload.allMembers and not member_ids:
        raise HTTPException(status_code=400, detail="Seleziona destinatari o «tutti»")
    if payload.allMembers:
        members = await db.members.find(
            {"memberRole": {"$in": list(MEMBER_ROLES)}, "slug": {"$exists": True, "$ne": ""}},
            {"_id": 0, "id": 1},
        ).to_list(2000)
        member_ids = [m["id"] for m in members]
    settings = await db.site_settings.find_one({"id": "site-settings"}, {"_id": 0}) or {}
    doc = {
        "id": str(uuid.uuid4()),
        "title": title,
        "bodyHtml": body if "<" in body else f"<p>{body}</p>",
        "createdAt": _now(),
        "createdBy": "admin",
        "authorName": settings.get("siteName", "AIA Legnano"),
        "allMembers": bool(payload.allMembers),
        "memberIds": member_ids if not payload.allMembers else [],
        "allowReplies": payload.allowReplies,
        "risposte": [],
        "attachments": [a.model_dump() for a in (payload.attachments or [])],
    }
    await db.comunicazioni_interne.insert_one(doc.copy())
    from ..member_notifications import schedule_comunicazione_notifications

    schedule_comunicazione_notifications(db, doc)
    return {"ok": True, "id": doc["id"], "destinatari": len(member_ids)}


@router.delete("/admin/comunicazioni/{comm_id}")
async def admin_delete_comunicazione(comm_id: str, admin=Depends(require_admin)):
    db = get_db()
    await db.comunicazioni_interne.delete_one({"id": comm_id})
    await db.comunicazioni_letture.delete_many({"comunicazioneId": comm_id})
    return {"ok": True}


