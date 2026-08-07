from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel, Field

from ...db import get_db
from ...security import (
    create_token,
    verify_password,
    hash_password,
    require_member,
    require_admin,
)
from ...uploads import (
    save_upload,
    IMAGE_EXTENSIONS,
    DEFAULT_IMAGE_MAX_BYTES,
    DEFAULT_MESSAGE_ATTACHMENT_MAX_BYTES,
)
from ...rate_limit import client_ip, enforce_rate_limit
from ...models import (
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
from ...portal_messaging import (
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
    count_unread_messages,
)
from ...designation_level import highest_championship_label
from ...portal_password import member_can_use_portal
from ...portal_member import member_public, is_staff_portal
from ...media_urls import resolve_media_fields, resolve_attachments
from ...paths import UPLOAD_DIR
from ...member_roles import MEMBER_ROLES, normalize_member
from ...comunicazioni_helpers import (
    comunicazione_destinatari,
    comunicazione_letture_map,
    comunicazione_letture_report,
)
from ...designation_filters import (
    current_season_label,
    season_label_from_iso,
    match_date_in_season_clause,
    distinct_seasons_from_dates,
    parse_season,
    event_date_in_season_clause,
    iso_datetime_in_season_clause,
    merge_mongo_queries,
)
from .deps import (
    PRESENZA_STATI,
    _now,
    _get_member,
    _presenza_map,
    _event_date_in_season_clause,
    _member_season_presenze_stats,
    _normalize_presenza_stato,
    _presenza_locked,
    _upsert_presenza,
)

router = APIRouter()


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
    from ...sanitize import sanitize_html

    body_html = body if "<" in body else f"<p>{body}</p>"
    body_html = sanitize_html(body_html)
    doc = {
        "id": str(uuid.uuid4()),
        "title": title,
        "bodyHtml": body_html,
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
    from ...member_notifications import schedule_comunicazione_notifications

    schedule_comunicazione_notifications(db, doc)
    return {"ok": True, "id": doc["id"], "destinatari": len(member_ids)}


@router.delete("/admin/comunicazioni/{comm_id}")
async def admin_delete_comunicazione(comm_id: str, admin=Depends(require_admin)):
    db = get_db()
    await db.comunicazioni_interne.delete_one({"id": comm_id})
    await db.comunicazioni_letture.delete_many({"comunicazioneId": comm_id})
    return {"ok": True}


