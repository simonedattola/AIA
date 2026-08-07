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


@router.get("/gallery/mine")
async def portal_gallery_mine(auth=Depends(require_member)):
    db = get_db()
    return await (
        db.gallery_images.find({"memberId": auth["memberId"]}, {"_id": 0})
        .sort("createdAt", -1)
        .to_list(200)
    )


@router.get("/gallery/categories")
async def portal_gallery_categories(auth=Depends(require_member)):
    from ...article_categories import get_public_article_categories

    db = get_db()
    return await get_public_article_categories(db)


@router.post("/gallery/upload")
async def portal_gallery_upload(
    file: UploadFile = File(...),
    caption: str = Form(""),
    category: str = Form(""),
    auth=Depends(require_member),
):
    _target, name, _size = await save_upload(
        file,
        allowed_ext=IMAGE_EXTENSIONS,
        max_bytes=DEFAULT_IMAGE_MAX_BYTES,
    )
    from ...article_categories import validate_member_category_choice
    from ...media_urls import resolve_media_url
    from ...gallery import save_uploaded_gallery_image

    db = get_db()
    try:
        category_resolved = await validate_member_category_choice(db, category)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    m = await _get_member(db, auth["memberId"])
    rel_path = f"/api/uploads/{name}"
    url = resolve_media_url(rel_path)
    member_name = f"{m.get('firstName', '')} {m.get('lastName', '')}".strip()
    doc = await save_uploaded_gallery_image(
        db,
        url=url,
        path=rel_path,
        caption=caption.strip(),
        status="pending",
        source="member",
        member_id=auth["memberId"],
        member_name=member_name,
        category=category_resolved,
    )
    return doc

