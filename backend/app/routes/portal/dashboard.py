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

# ---- Dashboard ----
async def _portal_events_for_member(
    db,
    mid: str,
    *,
    from_date: str | None = None,
    current_season: bool = False,
    limit: int | None = None,
) -> list[dict]:
    from ...event_access import member_invited_to_event

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
        from ...designation_queries import find_next_member_designation
        from ...member_roles import normalize_member

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
    from ...portal_messaging import count_unread_messages

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


