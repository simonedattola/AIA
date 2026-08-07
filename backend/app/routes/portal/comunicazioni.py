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


