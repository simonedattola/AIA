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
    from ...designation_enrich import enrich_designation, build_member_lookups
    from ...member_roles import legacy_arbitri_query

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


