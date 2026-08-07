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


class TestimonialSubmit(BaseModel):
    quote: str
    role: str = ""


@router.post("/upload-foto")
async def portal_upload_foto(file: UploadFile = File(...), auth=Depends(require_member)):
    _target, name, _size = await save_upload(
        file,
        allowed_ext=IMAGE_EXTENSIONS,
        max_bytes=DEFAULT_IMAGE_MAX_BYTES,
    )
    from ...media_urls import resolve_media_url

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
    from ...media_urls import upload_basename

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
    from ...models import Testimonial

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


