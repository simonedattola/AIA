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