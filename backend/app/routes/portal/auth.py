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
        from ...portal_credentials import ensure_member_portal_credentials
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
        from ...portal_password import validate_portal_password

        pwd_err = validate_portal_password(payload.newPassword)
        if pwd_err:
            raise HTTPException(status_code=400, detail=pwd_err)
        upd["passwordHash"] = hash_password(payload.newPassword)
    await db.members.update_one({"id": m["id"]}, {"$set": upd})
    m.update(upd)
    resolve_media_fields(m)
    return member_public(m)

