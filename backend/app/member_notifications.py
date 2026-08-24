"""Notifiche email agli associati (comunicazioni, messaggi)."""

from __future__ import annotations

import asyncio
import logging
import os
import re

from .mailer import (
    render_comunicazione_email,
    render_comunicazione_reply_member_email,
    render_comunicazione_reply_staff_email,
    render_message_email,
    send_email,
)
from .staff_email import staff_notify_email
from .person_names import format_person_name

logger = logging.getLogger(__name__)

PORTAL_BASE_URL = os.environ.get("PORTAL_FRONTEND_URL", "http://localhost:3000").rstrip(
    "/"
)


def _member_email(member: dict) -> str:
    return (member.get("email") or "").strip()


def _strip_html(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html or "", flags=re.I)
    text = re.sub(r"</p>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


async def _send_to_member(member: dict, subject: str, html: str) -> bool:
    email = _member_email(member)
    if not email:
        return False
    return await send_email(email, subject, html)


async def notify_comunicazione_recipients(db, comm: dict) -> int:
    """Invia email ai destinatari che hanno attivato le notifiche comunicazioni."""
    from .comunicazioni_helpers import comunicazione_destinatari

    destinatari = await comunicazione_destinatari(db, comm)
    sent = 0
    link = f"{PORTAL_BASE_URL}/area-associati/comunicazioni-interne"
    for member in destinatari:
        if not member.get("emailNotifyComunicazioni"):
            continue
        nome = format_person_name(member.get("firstName"), member.get("lastName"))
        subject = f"Nuova comunicazione: {comm.get('title', 'AIA Legnano')}"
        html = render_comunicazione_email(
            title=comm.get("title", ""),
            body_preview=_strip_html(comm.get("bodyHtml", ""))[:400],
            member_name=nome,
            link=link,
        )
        if await _send_to_member(member, subject, html):
            sent += 1
    if sent:
        logger.info(
            "Notifiche comunicazione inviate: %s (comm=%s)", sent, comm.get("id")
        )
    return sent


async def notify_direct_message(
    db, recipient_id: str, sender_name: str, preview: str
) -> bool:
    member = await db.members.find_one({"id": recipient_id}, {"_id": 0})
    if not member or not member.get("emailNotifyMessages"):
        return False
    link = f"{PORTAL_BASE_URL}/area-associati/messaggi"
    subject = f"Nuovo messaggio da {sender_name}"
    nome = format_person_name(member.get("firstName"), member.get("lastName"))
    html = render_message_email(
        member_name=nome,
        sender_name=sender_name,
        preview=(preview or "Hai ricevuto un nuovo messaggio.")[:300],
        link=link,
        context="messaggio privato",
    )
    return await _send_to_member(member, subject, html)


async def notify_group_message(
    db,
    group_id: str,
    sender_id: str,
    sender_name: str,
    group_name: str,
    preview: str,
) -> int:
    group = await db.chat_gruppi.find_one(
        {"id": group_id}, {"_id": 0, "memberIds": 1, "nome": 1}
    )
    if not group:
        return 0
    link = f"{PORTAL_BASE_URL}/area-associati/messaggi"
    sent = 0
    for mid in group.get("memberIds") or []:
        if mid == sender_id:
            continue
        member = await db.members.find_one({"id": mid}, {"_id": 0})
        if not member or not member.get("emailNotifyMessages"):
            continue
        nome = format_person_name(member.get("firstName"), member.get("lastName"))
        gname = group_name or group.get("nome") or "Gruppo"
        subject = f"Nuovo messaggio nel gruppo {gname}"
        html = render_message_email(
            member_name=nome,
            sender_name=sender_name,
            preview=(preview or "Nuovo messaggio nel gruppo.")[:300],
            link=link,
            context=f"gruppo «{gname}»",
        )
        if await _send_to_member(member, subject, html):
            sent += 1
    return sent


def schedule_comunicazione_notifications(db, comm: dict) -> None:
    """Fire-and-forget dopo creazione comunicazione."""
    asyncio.create_task(notify_comunicazione_recipients(db, comm))


async def notify_comunicazione_reply(
    db, comm: dict, *, author_id: str, author_name: str, reply_text: str
) -> int:
    """Avvisa la sezione + gli associati opt-in (escluso chi ha commentato)."""
    link = f"{PORTAL_BASE_URL}/area-associati/comunicazioni-interne"
    title = comm.get("title") or "Comunicazione"
    preview = (reply_text or "")[:400]
    sent = 0

    staff = await staff_notify_email(db)
    if staff:
        html = render_comunicazione_reply_staff_email(
            title=title,
            author_name=author_name,
            reply_text=preview,
            link=link,
        )
        if await send_email(
            staff,
            f"Commento su «{title}» da {author_name}",
            html,
        ):
            sent += 1

    from .comunicazioni_helpers import comunicazione_destinatari

    for member in await comunicazione_destinatari(db, comm):
        if member.get("id") == author_id:
            continue
        if not member.get("emailNotifyComunicazioni"):
            continue
        nome = format_person_name(member.get("firstName"), member.get("lastName"))
        html = render_comunicazione_reply_member_email(
            member_name=nome,
            title=title,
            author_name=author_name,
            reply_text=preview,
            link=link,
        )
        if await _send_to_member(member, f"Nuovo commento su «{title}»", html):
            sent += 1
    return sent


def schedule_comunicazione_reply_notification(
    db, comm: dict, *, author_id: str, author_name: str, reply_text: str
) -> None:
    async def _run():
        try:
            await notify_comunicazione_reply(
                db,
                comm,
                author_id=author_id,
                author_name=author_name,
                reply_text=reply_text,
            )
        except Exception:
            logger.exception("Invio notifica commento comunicazione fallito")

    asyncio.create_task(_run())


def schedule_message_notification(
    db,
    *,
    kind: str,
    recipient_id: str | None,
    group_id: str | None,
    sender_id: str,
    sender_name: str,
    group_name: str = "",
    preview: str,
) -> None:
    async def _run():
        try:
            if kind == "direct" and recipient_id:
                await notify_direct_message(db, recipient_id, sender_name, preview)
            elif kind == "group" and group_id:
                await notify_group_message(
                    db, group_id, sender_id, sender_name, group_name, preview
                )
        except Exception:
            logger.exception("Invio notifica messaggio fallito")

    asyncio.create_task(_run())
