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


@router.get("/admin/presenze/associati/{member_id}")
async def admin_presenze_associato(member_id: str, admin=Depends(require_admin)):
    db = get_db()
    from ...event_access import member_invited_to_event

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
    from ...event_access import event_invited_member_ids
    from ...member_roles import normalize_member

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

