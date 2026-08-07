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

# ---- Messaggi interni (chat dirette + gruppi) ----
@router.get("/messaggi/conversazioni")
async def portal_conversazioni(auth=Depends(require_member)):
    return await list_conversations(get_db(), auth["memberId"])


@router.get("/messaggi/conversazioni/{chat_id}")
async def portal_conversazione(chat_id: str, auth=Depends(require_member)):
    return await get_conversation(get_db(), chat_id, auth["memberId"], _now())


@router.delete("/messaggi/conversazioni/{chat_id}")
async def portal_elimina_conversazione(chat_id: str, auth=Depends(require_member)):
    return await delete_conversation_for_member(get_db(), chat_id, auth["memberId"], _now())


@router.get("/messaggi/conversazioni/{chat_id}/contatto")
async def portal_contatto_chat(chat_id: str, auth=Depends(require_member)):
    kind, target_id = parse_chat_id(chat_id)
    if kind != "direct":
        raise HTTPException(status_code=400, detail="Disponibile solo per chat private")
    return await get_contact_info(get_db(), target_id, auth["memberId"])


@router.get("/messaggi/conversazioni/{chat_id}/gruppo")
async def portal_info_gruppo(chat_id: str, auth=Depends(require_member)):
    return await get_group_info(get_db(), chat_id, auth["memberId"])


@router.post("/messaggi/conversazioni/{chat_id}")
async def portal_invia_in_conversazione(
    chat_id: str, payload: MessaggioInternoCreate, auth=Depends(require_member)
):
    return await send_message(
        get_db(), chat_id, auth["memberId"], payload.model_dump(), _now(), _get_member
    )


@router.post("/messaggi/allegati")
async def portal_upload_allegato(file: UploadFile = File(...), auth=Depends(require_member)):
    allowed = {
        ".jpg", ".jpeg", ".png", ".webp", ".gif",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".zip",
    }
    from pathlib import Path as _Path

    ext = _Path(file.filename or "").suffix.lower() or ".bin"
    _target, name, _size = await save_upload(
        file,
        allowed_ext=allowed,
        max_bytes=DEFAULT_MESSAGE_ATTACHMENT_MAX_BYTES,
        name_prefix="msg_",
    )
    from ...media_urls import resolve_media_url

    rel_path = f"/api/uploads/{name}"
    mime = file.content_type or ""
    tipo = "image" if mime.startswith("image/") or ext in IMAGE_EXTENSIONS else "file"
    return {
        "attachmentUrl": rel_path,
        "attachmentUrlResolved": resolve_media_url(rel_path),
        "attachmentName": file.filename or name,
        "attachmentMime": mime,
        "tipo": tipo,
    }


@router.put("/messaggi/{msg_id}")
async def portal_modifica_messaggio(
    msg_id: str, payload: MessaggioModificaBody, auth=Depends(require_member)
):
    return await edit_message(get_db(), msg_id, auth["memberId"], payload.testo, _now())


@router.delete("/messaggi/{msg_id}")
async def portal_elimina_messaggio(msg_id: str, auth=Depends(require_member)):
    return await delete_message(get_db(), msg_id, auth["memberId"], _now())


@router.post("/messaggi/{msg_id}/reazioni")
async def portal_reazione_messaggio(
    msg_id: str, payload: MessaggioReazioneBody, auth=Depends(require_member)
):
    return await toggle_reaction(
        get_db(), msg_id, auth["memberId"], payload.emoji, _now(), _get_member
    )


@router.post("/messaggi/gruppi")
async def portal_crea_gruppo(payload: GruppoChatCreate, auth=Depends(require_member)):
    g = await create_group(
        get_db(),
        auth["memberId"],
        payload.name,
        payload.memberIds or [],
        _now(),
        photo_url=payload.photoUrl or "",
        description=payload.description or "",
    )
    return {**g, "chatId": chat_id_for_group(g["id"])}


@router.put("/messaggi/gruppi/{gruppo_id}")
async def portal_aggiorna_gruppo(
    gruppo_id: str, payload: GruppoChatUpdate, auth=Depends(require_member)
):
    data = payload.model_dump(exclude_unset=True)
    return await update_group(get_db(), gruppo_id, auth["memberId"], data, _now())


@router.post("/messaggi/gruppi/{gruppo_id}/esci")
async def portal_esci_gruppo(gruppo_id: str, auth=Depends(require_member)):
    return await leave_group(get_db(), gruppo_id, auth["memberId"], _now())


@router.get("/messaggi")
async def portal_messaggi(auth=Depends(require_member)):
    return await portal_conversazioni(auth)


@router.get("/messaggi/associati")
async def portal_lista_associati(auth=Depends(require_member)):
    """Profili associati per nuove chat e gruppi (solo tra associati)."""
    db = get_db()
    items = await db.members.find(
        {"memberRole": {"$in": list(MEMBER_ROLES)}, "slug": {"$exists": True, "$ne": ""}},
        {"_id": 0, "id": 1, "firstName": 1, "lastName": 1, "memberRole": 1, "photoUrl": 1, "observerType": 1},
    ).sort([("lastName", 1), ("firstName", 1)]).to_list(500)
    for it in items:
        normalize_member(it)
        resolve_media_fields(it)
    from ...member_roles import member_role_label

    return [
        {
            "id": i["id"],
            "firstName": i.get("firstName"),
            "lastName": i.get("lastName"),
            "photoUrl": i.get("photoUrl"),
            "roleLabel": member_role_label(i.get("memberRole"), i.get("observerType")),
        }
        for i in items
        if i["id"] != auth["memberId"]
    ]

