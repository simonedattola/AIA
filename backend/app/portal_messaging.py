"""Messaggistica associati — chat dirette, gruppi, allegati, reazioni."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import HTTPException

from .media_urls import resolve_media_fields, resolve_media_url
from .member_roles import MEMBER_ROLES, normalize_member

ALLOWED_EMOJI = {"👍", "❤️", "😂", "😮", "😢", "🙏", "🔥", "👏"}
MESSAGE_EDIT_WINDOW = timedelta(minutes=15)


def group_photo_url(g: dict) -> str:
    raw = (g.get("photoUrl") or "").strip()
    return resolve_media_url(raw) if raw else ""


def _parse_iso(ts: str) -> Optional[datetime]:
    if not ts:
        return None
    try:
        normalized = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def message_editable(msg: dict, mid: str, now_iso: Optional[str] = None) -> bool:
    """True se il mittente può ancora modificare un messaggio di testo (entro 15 minuti)."""
    if msg.get("mittenteId") != mid:
        return False
    if msg.get("deletedAt"):
        return False
    if (msg.get("tipo") or "text") != "text":
        return False
    created = _parse_iso(msg.get("createdAt") or "")
    if not created:
        return False
    now = _parse_iso(now_iso) if now_iso else datetime.now(timezone.utc)
    if not now:
        now = datetime.now(timezone.utc)
    return now - created <= MESSAGE_EDIT_WINDOW


async def group_members_list(db, member_ids: list[str]) -> list[dict]:
    out = []
    for uid in member_ids or []:
        d = await member_display(db, uid)
        out.append({"id": uid, "name": d["name"], "photoUrl": d["photo"]})
    return out


async def group_members_summary(db, member_ids: list[str], *, limit: int = 12) -> dict:
    members = await group_members_list(db, member_ids)
    names = [m["name"] for m in members if m.get("name")]
    extra = max(0, len(member_ids) - limit)
    shown = names[:limit]
    line = ", ".join(shown)
    if extra:
        line = f"{line}, +{extra}" if line else f"+{extra}"
    return {
        "members": members,
        "memberNames": shown,
        "memberNamesLine": line,
        "memberCount": len(member_ids),
    }


def chat_id_for_group(gruppo_id: str) -> str:
    return f"g:{gruppo_id}"


def parse_chat_id(chat_id: str) -> tuple[str, str]:
    if chat_id.startswith("g:"):
        return "group", chat_id[2:]
    return "direct", chat_id


def _direct_filter(mid: str, other_id: str) -> dict:
    return {
        "$and": [
            {"$or": [{"gruppoId": {"$exists": False}}, {"gruppoId": None}, {"gruppoId": ""}]},
            {
                "$or": [
                    {"mittenteId": mid, "destinatarioId": other_id},
                    {"mittenteId": other_id, "destinatarioId": mid},
                ]
            },
        ]
    }


async def member_display(db, member_id: str, *, contact_panel: bool = False) -> dict[str, Any]:
    m = await db.members.find_one(
        {"id": member_id},
        {
            "_id": 0,
            "id": 1,
            "slug": 1,
            "firstName": 1,
            "lastName": 1,
            "photoUrl": 1,
            "email": 1,
            "phone": 1,
            "emailVisibile": 1,
            "telefonoVisibile": 1,
            "category": 1,
            "memberRole": 1,
            "observerType": 1,
            "bio": 1,
        },
    )
    if not m:
        return {
            "id": member_id,
            "firstName": "Associato",
            "lastName": "",
            "name": "Associato",
            "photo": "",
            "slug": "",
            "email": "",
            "phone": "",
        }
    normalize_member(m)
    resolve_media_fields(m)
    from .member_roles import member_role_label

    email = phone = ""
    if contact_panel:
        if m.get("emailVisibile"):
            email = (m.get("email") or "").strip()
        if m.get("telefonoVisibile"):
            phone = (m.get("phone") or "").strip()
    else:
        email = (m.get("email") or "").strip()
        phone = (m.get("phone") or "").strip()

    return {
        "id": m["id"],
        "slug": m.get("slug") or "",
        "firstName": m.get("firstName") or "",
        "lastName": m.get("lastName") or "",
        "name": f"{m.get('firstName', '')} {m.get('lastName', '')}".strip() or "Associato",
        "photo": m.get("photoUrl") or "",
        "email": email,
        "phone": phone,
        "category": m.get("category") or "",
        "roleLabel": member_role_label(m.get("memberRole"), m.get("observerType")),
        "bio": (m.get("bio") or "").strip(),
    }


def message_preview(msg: dict) -> str:
    if msg.get("deletedAt"):
        return "Messaggio eliminato"
    t = msg.get("tipo") or "text"
    if t == "image":
        return "📷 Foto"
    if t == "file":
        return f"📎 {msg.get('attachmentName') or 'File'}"
    return (msg.get("testo") or "")[:80]


def message_read_status(msg: dict, my_id: str, is_group: bool, group_size: int) -> str:
    if msg.get("mittenteId") != my_id:
        return ""
    if is_group:
        others = max(0, group_size - 1)
        read_by = [x for x in (msg.get("lettiDa") or []) if x != my_id]
        if others > 0 and len(read_by) >= others:
            return "read"
        return "delivered"
    if msg.get("letto"):
        return "read"
    return "delivered"


async def _read_info_for_message(db, msg: dict, my_id: str, is_group: bool, group_size: int) -> dict:
    if msg.get("mittenteId") != my_id:
        return {}
    if is_group:
        readers = []
        for uid in msg.get("lettiDa") or []:
            if uid == my_id:
                continue
            d = await member_display(db, uid)
            readers.append({"id": uid, "name": d["name"]})
        return {"type": "group", "readers": readers, "total": len(readers), "expected": max(0, group_size - 1)}
    if msg.get("letto"):
        return {"type": "read", "at": msg.get("lettoAt"), "by": msg.get("destinatarioNome")}
    return {"type": "delivered"}


async def enrich_message(
    db, msg: dict, my_id: str, is_group: bool, group_size: int, msg_by_id: dict[str, dict]
) -> dict:
    out = dict(msg)
    if out.get("attachmentUrl"):
        out["attachmentUrlResolved"] = resolve_media_url(out["attachmentUrl"])
    if out.get("deletedAt"):
        out["isDeleted"] = True
    rid = out.get("replyToId")
    if rid and rid in msg_by_id:
        r = msg_by_id[rid]
        out["replyTo"] = {
            "id": r["id"],
            "mittenteNome": r.get("mittenteNome"),
            "testo": "Messaggio eliminato" if r.get("deletedAt") else (r.get("testo") or message_preview(r)),
            "tipo": r.get("tipo") or "text",
        }
    reactions = out.get("reactions") or []
    grouped: dict[str, list] = {}
    for rx in reactions:
        e = rx.get("emoji")
        if e:
            grouped.setdefault(e, []).append(rx.get("memberName") or "")
    out["reactionSummary"] = [{"emoji": e, "count": len(names), "names": names} for e, names in grouped.items()]
    out["myReaction"] = next((rx.get("emoji") for rx in reactions if rx.get("memberId") == my_id), None)
    out["readStatus"] = message_read_status(out, my_id, is_group, group_size)
    out["readInfo"] = await _read_info_for_message(db, out, my_id, is_group, group_size)
    out["canEdit"] = message_editable(out, my_id)
    return out


async def _hidden_chats_map(db, mid: str) -> dict[str, str]:
    rows = await db.chat_hidden.find({"memberId": mid}, {"_id": 0, "chatId": 1, "hiddenAt": 1}).to_list(500)
    return {r["chatId"]: r.get("hiddenAt") or "" for r in rows}


async def unhide_conversation(db, chat_id: str, mid: str) -> None:
    kind, target_id = parse_chat_id(chat_id)
    cid = chat_id if kind == "group" else target_id
    await db.chat_hidden.delete_one({"memberId": mid, "chatId": cid})


async def hide_direct_conversation(db, peer_id: str, mid: str, now_iso: str) -> dict:
    if peer_id == "admin" or peer_id == mid:
        raise HTTPException(status_code=400, detail="Conversazione non valida")
    await db.chat_hidden.update_one(
        {"memberId": mid, "chatId": peer_id},
        {"$set": {"hiddenAt": now_iso, "updatedAt": now_iso}},
        upsert=True,
    )
    return {"deleted": True, "chatId": peer_id, "type": "direct"}


async def delete_conversation_for_member(db, chat_id: str, mid: str, now_iso: str) -> dict:
    """Elimina chat/gruppo per l'associato: nasconde le chat private, esce dai gruppi."""
    kind, target_id = parse_chat_id(chat_id)
    if kind == "group":
        result = await leave_group(db, target_id, mid, now_iso)
        result["deleted"] = True
        result["type"] = "group"
        return result
    return await hide_direct_conversation(db, target_id, mid, now_iso)


async def common_groups(db, mid: str, other_id: str) -> list[dict]:
    my_groups = await db.chat_gruppi.find({"memberIds": mid}, {"_id": 0}).to_list(200)
    out = []
    for g in my_groups:
        if other_id in (g.get("memberIds") or []):
            out.append({
                "chatId": chat_id_for_group(g["id"]),
                "gruppoId": g["id"],
                "name": g.get("name") or "Gruppo",
                "memberCount": len(g.get("memberIds") or []),
            })
    return out


async def get_contact_info(db, peer_id: str, mid: str) -> dict:
    if peer_id == "admin":
        raise HTTPException(status_code=404, detail="Contatto non trovato")
    disp = await member_display(db, peer_id, contact_panel=True)
    return {
        **disp,
        "commonGroups": await common_groups(db, mid, peer_id),
    }


async def list_conversations(db, mid: str) -> list[dict[str, Any]]:
    rows: dict[str, dict] = {}

    direct_msgs = await db.messaggi_interni.find(
        {
            "$and": [
                {"$or": [{"gruppoId": {"$exists": False}}, {"gruppoId": None}, {"gruppoId": ""}]},
                {"$or": [{"mittenteId": mid}, {"destinatarioId": mid}]},
                {"destinatarioId": {"$ne": "admin"}},
                {"mittenteId": {"$ne": "admin"}},
            ]
        },
        {"_id": 0},
    ).sort("createdAt", -1).to_list(5000)

    for m in direct_msgs:
        pid, pname = (
            (m.get("destinatarioId"), m.get("destinatarioNome"))
            if m.get("mittenteId") == mid
            else (m.get("mittenteId"), m.get("mittenteNome"))
        )
        if not pid or pid == "admin" or m.get("gruppoId"):
            continue
        cid = pid
        unread = (
            m.get("destinatarioId") == mid
            and not m.get("letto")
            and not m.get("deletedAt")
        )
        if cid not in rows:
            rows[cid] = {
                "chatId": cid,
                "type": "direct",
                "isGroup": False,
                "peerName": pname or "Associato",
                "lastMessage": message_preview(m),
                "lastAt": m.get("createdAt"),
                "unreadCount": 1 if unread else 0,
                "memberCount": 2,
            }
        elif unread:
            rows[cid]["unreadCount"] += 1

    groups = await db.chat_gruppi.find({"memberIds": mid}, {"_id": 0}).to_list(200)
    for g in groups:
        gid = g["id"]
        cid = chat_id_for_group(gid)
        last = await db.messaggi_interni.find_one({"gruppoId": gid}, {"_id": 0}, sort=[("createdAt", -1)])
        unread = await db.messaggi_interni.count_documents(
            {
                "gruppoId": gid,
                "mittenteId": {"$ne": mid},
                "deletedAt": {"$exists": False},
                "$or": [{"lettiDa": {"$exists": False}}, {"lettiDa": {"$nin": [mid]}}],
            }
        )
        summary = await group_members_summary(db, g.get("memberIds") or [])
        rows[cid] = {
            "chatId": cid,
            "type": "group",
            "isGroup": True,
            "gruppoId": gid,
            "peerName": g.get("name") or "Gruppo",
            "peerPhoto": group_photo_url(g),
            "lastMessage": message_preview(last) if last else "",
            "lastAt": (last.get("createdAt") if last else g.get("createdAt")),
            "unreadCount": unread,
            "memberCount": summary["memberCount"],
            "memberNamesLine": summary["memberNamesLine"],
        }

    for r in rows.values():
        if r["type"] == "direct":
            disp = await member_display(db, r["chatId"])
            r["peerPhoto"] = disp["photo"]

    hidden = await _hidden_chats_map(db, mid)
    visible = []
    for r in rows.values():
        hid = hidden.get(r["chatId"])
        if hid:
            last = r.get("lastAt") or ""
            if not last or last <= hid:
                continue
        visible.append(r)

    return sorted(visible, key=lambda x: x.get("lastAt") or "", reverse=True)


async def count_unread_messages(db, mid: str) -> int:
    """Totale messaggi non letti (chat dirette + gruppi)."""
    conversations = await list_conversations(db, mid)
    return sum(int(c.get("unreadCount") or 0) for c in conversations)


async def _load_messages_enriched(db, msgs: list, mid: str, is_group: bool, group_size: int) -> list[dict]:
    msg_by_id = {m["id"]: m for m in msgs}
    out = []
    for m in msgs:
        out.append(await enrich_message(db, m, mid, is_group, group_size, msg_by_id))
    return out


async def get_conversation(db, chat_id: str, mid: str, now_iso: str) -> dict[str, Any]:
    await unhide_conversation(db, chat_id, mid)
    kind, target_id = parse_chat_id(chat_id)
    if kind == "direct":
        if target_id == "admin":
            raise HTTPException(status_code=404, detail="Conversazione non trovata")
        msgs = await db.messaggi_interni.find(_direct_filter(mid, target_id), {"_id": 0}).sort("createdAt", 1).to_list(500)
        await db.messaggi_interni.update_many(
            {"mittenteId": target_id, "destinatarioId": mid, "letto": False},
            {"$set": {"letto": True, "lettoAt": now_iso}},
        )
        disp = await member_display(db, target_id)
        enriched = await _load_messages_enriched(db, msgs, mid, False, 2)
        return {
            "chatId": target_id,
            "type": "direct",
            "isGroup": False,
            "peerId": disp["id"],
            "peerName": disp["name"],
            "peerPhoto": disp["photo"],
            "peerFirstName": disp["firstName"],
            "peerLastName": disp["lastName"],
            "memberCount": 2,
            "messages": enriched,
        }

    g = await db.chat_gruppi.find_one({"id": target_id, "memberIds": mid}, {"_id": 0})
    if not g:
        raise HTTPException(status_code=404, detail="Gruppo non trovato")
    gid = g["id"]
    msgs = await db.messaggi_interni.find({"gruppoId": gid}, {"_id": 0}).sort("createdAt", 1).to_list(500)
    await db.messaggi_interni.update_many(
        {
            "gruppoId": gid,
            "mittenteId": {"$ne": mid},
            "$or": [{"lettiDa": {"$exists": False}}, {"lettiDa": {"$nin": [mid]}}],
        },
        {"$addToSet": {"lettiDa": mid}},
    )
    summary = await group_members_summary(db, g.get("memberIds") or [])
    enriched = await _load_messages_enriched(db, msgs, mid, True, summary["memberCount"])
    return {
        "chatId": chat_id_for_group(gid),
        "type": "group",
        "isGroup": True,
        "gruppoId": gid,
        "peerName": g.get("name") or "Gruppo",
        "peerPhoto": group_photo_url(g),
        "description": (g.get("description") or "").strip(),
        "memberCount": summary["memberCount"],
        "memberNamesLine": summary["memberNamesLine"],
        "members": summary["members"],
        "messages": enriched,
    }


async def get_group_info(db, chat_id: str, mid: str) -> dict[str, Any]:
    kind, target_id = parse_chat_id(chat_id)
    if kind != "group":
        raise HTTPException(status_code=400, detail="Non è un gruppo")
    g = await db.chat_gruppi.find_one({"id": target_id, "memberIds": mid}, {"_id": 0})
    if not g:
        raise HTTPException(status_code=404, detail="Gruppo non trovato")
    summary = await group_members_summary(db, g.get("memberIds") or [], limit=500)
    return {
        "id": g["id"],
        "chatId": chat_id_for_group(g["id"]),
        "name": g.get("name") or "Gruppo",
        "photo": group_photo_url(g),
        "photoUrl": (g.get("photoUrl") or "").strip(),
        "description": (g.get("description") or "").strip(),
        "memberCount": summary["memberCount"],
        "memberNamesLine": summary["memberNamesLine"],
        "members": summary["members"],
        "createdBy": g.get("createdBy"),
    }


async def update_group(db, gruppo_id: str, mid: str, payload: dict, now_iso: str) -> dict:
    g = await db.chat_gruppi.find_one({"id": gruppo_id, "memberIds": mid}, {"_id": 0})
    if not g:
        raise HTTPException(status_code=404, detail="Gruppo non trovato")
    updates: dict[str, Any] = {"updatedAt": now_iso}
    if payload.get("name") is not None:
        name = (payload.get("name") or "").strip()
        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Nome gruppo troppo corto")
        updates["name"] = name
    if payload.get("description") is not None:
        updates["description"] = (payload.get("description") or "").strip()
    if payload.get("photoUrl") is not None:
        updates["photoUrl"] = (payload.get("photoUrl") or "").strip()
    await db.chat_gruppi.update_one({"id": gruppo_id}, {"$set": updates})
    g = await db.chat_gruppi.find_one({"id": gruppo_id}, {"_id": 0})
    return await get_group_info(db, chat_id_for_group(gruppo_id), mid)


async def leave_group(db, gruppo_id: str, mid: str, now_iso: str) -> dict:
    g = await db.chat_gruppi.find_one({"id": gruppo_id, "memberIds": mid}, {"_id": 0})
    if not g:
        raise HTTPException(status_code=404, detail="Gruppo non trovato")
    ids = [x for x in (g.get("memberIds") or []) if x != mid]
    if len(ids) < 2:
        await db.chat_gruppi.delete_one({"id": gruppo_id})
        return {"left": True, "dissolved": True, "chatId": chat_id_for_group(gruppo_id)}
    await db.chat_gruppi.update_one(
        {"id": gruppo_id},
        {"$set": {"memberIds": ids, "updatedAt": now_iso}},
    )
    return {"left": True, "dissolved": False, "chatId": chat_id_for_group(gruppo_id)}


def _base_message_doc(mid: str, mitt_nome: str, now_iso: str, **extra) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "mittenteId": mid,
        "mittenteNome": mitt_nome,
        "testo": "",
        "tipo": "text",
        "attachmentUrl": "",
        "attachmentName": "",
        "attachmentMime": "",
        "replyToId": None,
        "reactions": [],
        "editedAt": None,
        "deletedAt": None,
        "letto": False,
        "lettoAt": None,
        "lettiDa": [mid],
        "createdAt": now_iso,
        **extra,
    }


async def send_message(db, chat_id: str, mid: str, payload: dict, now_iso: str, get_member_fn) -> dict:
    await unhide_conversation(db, chat_id, mid)
    testo = (payload.get("testo") or "").strip()
    tipo = (payload.get("tipo") or "text").lower()
    attachment_url = (payload.get("attachmentUrl") or "").strip()
    reply_to_id = (payload.get("replyToId") or "").strip() or None

    if tipo == "text" and not testo and not attachment_url:
        raise HTTPException(status_code=400, detail="Messaggio vuoto")

    mitt = await get_member_fn(db, mid)
    mitt_nome = f"{mitt.get('firstName', '')} {mitt.get('lastName', '')}".strip()
    kind, target_id = parse_chat_id(chat_id)
    group_size = 2

    if attachment_url:
        if not tipo or tipo == "text":
            mime = (payload.get("attachmentMime") or "").lower()
            tipo = "image" if mime.startswith("image/") else "file"
    elif tipo != "text":
        tipo = "text"

    extra = {
        "testo": testo,
        "tipo": tipo,
        "attachmentUrl": attachment_url,
        "attachmentName": (payload.get("attachmentName") or "").strip(),
        "attachmentMime": (payload.get("attachmentMime") or "").strip(),
        "replyToId": reply_to_id,
    }

    if kind == "direct":
        if target_id == "admin":
            raise HTTPException(status_code=400, detail="Chat non disponibile")
        dest = await db.members.find_one({"id": target_id}, {"_id": 0})
        if not dest:
            raise HTTPException(status_code=404, detail="Destinatario non trovato")
        doc = _base_message_doc(
            mid,
            mitt_nome,
            now_iso,
            destinatarioId=target_id,
            destinatarioNome=f"{dest.get('firstName', '')} {dest.get('lastName', '')}".strip(),
            gruppoId=None,
            lettiDa=[],
            **extra,
        )
    else:
        gruppo = await db.chat_gruppi.find_one({"id": target_id, "memberIds": mid}, {"_id": 0})
        if not gruppo:
            raise HTTPException(status_code=404, detail="Gruppo non trovato")
        doc = _base_message_doc(
            mid,
            mitt_nome,
            now_iso,
            destinatarioId=None,
            destinatarioNome=None,
            gruppoId=target_id,
            **extra,
        )
        group_size = len(gruppo.get("memberIds") or [])

    if reply_to_id:
        valid = await _message_in_chat(db, reply_to_id, mid, kind, target_id)
        if not valid:
            raise HTTPException(status_code=400, detail="Messaggio di risposta non valido")

    await db.messaggi_interni.insert_one(doc.copy())

    preview = testo or doc.get("attachmentName") or "Allegato"
    from .member_notifications import schedule_message_notification

    if kind == "direct":
        schedule_message_notification(
            db,
            kind="direct",
            recipient_id=target_id,
            group_id=None,
            sender_id=mid,
            sender_name=mitt_nome,
            preview=preview,
        )
    else:
        schedule_message_notification(
            db,
            kind="group",
            recipient_id=None,
            group_id=target_id,
            sender_id=mid,
            sender_name=mitt_nome,
            group_name=gruppo.get("nome") or gruppo.get("name") or "",
            preview=preview,
        )

    enriched = await enrich_message(db, doc, mid, kind == "group", group_size, {doc["id"]: doc})
    return enriched


async def _message_in_chat(db, msg_id: str, mid: str, kind: str, target_id: str) -> bool:
    m = await db.messaggi_interni.find_one({"id": msg_id}, {"_id": 0})
    if not m:
        return False
    if kind == "direct":
        o = m.get("destinatarioId")
        s = m.get("mittenteId")
        return target_id in (o, s) and mid in (o, s)
    return m.get("gruppoId") == target_id


async def _get_message_for_user(db, msg_id: str, mid: str) -> tuple[dict, str, str]:
    m = await db.messaggi_interni.find_one({"id": msg_id}, {"_id": 0})
    if not m:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
    if m.get("gruppoId"):
        g = await db.chat_gruppi.find_one({"id": m["gruppoId"], "memberIds": mid}, {"_id": 0, "id": 1})
        if not g:
            raise HTTPException(status_code=403, detail="Non autorizzato")
        return m, "group", m["gruppoId"]
    o, s = m.get("destinatarioId"), m.get("mittenteId")
    if mid not in (o, s):
        raise HTTPException(status_code=403, detail="Non autorizzato")
    other = o if s == mid else s
    return m, "direct", other


async def edit_message(db, msg_id: str, mid: str, testo: str, now_iso: str) -> dict:
    testo = (testo or "").strip()
    if not testo:
        raise HTTPException(status_code=400, detail="Testo obbligatorio")
    m, kind, target = await _get_message_for_user(db, msg_id, mid)
    if m.get("mittenteId") != mid:
        raise HTTPException(status_code=403, detail="Solo il mittente può modificare")
    if m.get("deletedAt"):
        raise HTTPException(status_code=400, detail="Messaggio eliminato")
    if (m.get("tipo") or "text") != "text":
        raise HTTPException(status_code=400, detail="Solo i messaggi di testo sono modificabili")
    if not message_editable(m, mid, now_iso):
        raise HTTPException(
            status_code=400,
            detail="La modifica è consentita solo entro 15 minuti dall'invio",
        )
    await db.messaggi_interni.update_one(
        {"id": msg_id},
        {"$set": {"testo": testo, "editedAt": now_iso}},
    )
    m["testo"] = testo
    m["editedAt"] = now_iso
    gs = 2
    if kind == "group":
        g = await db.chat_gruppi.find_one({"id": target}, {"_id": 0})
        gs = len(g.get("memberIds") or []) if g else 2
    return await enrich_message(db, m, mid, kind == "group", gs, {msg_id: m})


async def delete_message(db, msg_id: str, mid: str, now_iso: str) -> dict:
    m, kind, target = await _get_message_for_user(db, msg_id, mid)
    if m.get("mittenteId") != mid:
        raise HTTPException(status_code=403, detail="Solo il mittente può eliminare")
    await db.messaggi_interni.update_one(
        {"id": msg_id},
        {"$set": {"deletedAt": now_iso, "testo": ""}},
    )
    m["deletedAt"] = now_iso
    m["testo"] = ""
    gs = 2
    if kind == "group":
        g = await db.chat_gruppi.find_one({"id": target}, {"_id": 0})
        gs = len(g.get("memberIds") or []) if g else 2
    return await enrich_message(db, m, mid, kind == "group", gs, {msg_id: m})


async def toggle_reaction(db, msg_id: str, mid: str, emoji: str, now_iso: str, get_member_fn) -> dict:
    emoji = (emoji or "").strip()
    if emoji not in ALLOWED_EMOJI:
        raise HTTPException(status_code=400, detail="Emoji non consentita")
    m, kind, target = await _get_message_for_user(db, msg_id, mid)
    if m.get("deletedAt"):
        raise HTTPException(status_code=400, detail="Messaggio eliminato")
    reactions = list(m.get("reactions") or [])
    existing = next((i for i, r in enumerate(reactions) if r.get("memberId") == mid and r.get("emoji") == emoji), None)
    if existing is not None:
        reactions.pop(existing)
    else:
        mitt = await get_member_fn(db, mid)
        nome = f"{mitt.get('firstName', '')} {mitt.get('lastName', '')}".strip()
        reactions = [r for r in reactions if r.get("memberId") != mid]
        reactions.append({"emoji": emoji, "memberId": mid, "memberName": nome, "createdAt": now_iso})
    await db.messaggi_interni.update_one({"id": msg_id}, {"$set": {"reactions": reactions}})
    m["reactions"] = reactions
    gs = 2
    if kind == "group":
        g = await db.chat_gruppi.find_one({"id": target}, {"_id": 0})
        gs = len(g.get("memberIds") or []) if g else 2
    return await enrich_message(db, m, mid, kind == "group", gs, {msg_id: m})


async def create_group(
    db,
    mid: str,
    name: str,
    member_ids: list[str],
    now_iso: str,
    *,
    photo_url: str = "",
    description: str = "",
) -> dict:
    name = (name or "").strip()
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Nome gruppo troppo corto")
    ids = list(dict.fromkeys([mid] + [x for x in member_ids if x and x != mid]))
    if len(ids) < 2:
        raise HTTPException(status_code=400, detail="Seleziona almeno un altro associato")
    valid = await db.members.count_documents(
        {
            "id": {"$in": ids},
            "memberRole": {"$in": list(MEMBER_ROLES)},
            "slug": {"$exists": True, "$ne": ""},
        }
    )
    if valid != len(ids):
        raise HTTPException(status_code=400, detail="Uno o più membri non validi")
    doc = {
        "id": str(uuid.uuid4()),
        "name": name,
        "memberIds": ids,
        "photoUrl": (photo_url or "").strip(),
        "description": (description or "").strip(),
        "createdBy": mid,
        "createdAt": now_iso,
    }
    await db.chat_gruppi.insert_one(doc.copy())
    return doc
