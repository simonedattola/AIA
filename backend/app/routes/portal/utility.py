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

# ---- Utility (materiale eventi, polo, link utili) ----
@router.get("/utility")
async def portal_utility(auth=Depends(require_member)):
    from ...media_urls import resolve_media_url, resolve_attachments
    from ...event_access import member_invited_to_event

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


