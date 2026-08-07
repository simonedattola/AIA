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
    from ...event_access import member_invited_to_event

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


