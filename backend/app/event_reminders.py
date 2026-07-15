"""Promemoria email prima degli eventi (preferenze associato)."""
from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from .db import get_db
from .event_access import member_invited_to_event
from .mailer import render_event_created_email, render_event_reminder_email, send_email

logger = logging.getLogger(__name__)

ROME = ZoneInfo("Europe/Rome")
EVENT_REMINDER_LEAD_HOURS = (24, 12, 6, 1)
EVENT_CREATED_LEAD_HOURS = 0
DEFAULT_EVENT_TIME = "09:00"
REMINDER_WINDOW = timedelta(minutes=10)
PORTAL_BASE_URL = os.environ.get("PORTAL_FRONTEND_URL", "http://localhost:3000").rstrip("/")


def normalize_event_time(value: str | None) -> str:
    text = (value or "").strip()
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", text)
    if not m:
        return DEFAULT_EVENT_TIME
    hour, minute = int(m.group(1)), int(m.group(2))
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return f"{hour:02d}:{minute:02d}"
    return DEFAULT_EVENT_TIME


def event_start_datetime(event: dict[str, Any], *, tz: ZoneInfo = ROME) -> datetime | None:
    date = (event.get("date") or "")[:10]
    if not date or len(date) < 10:
        return None
    try:
        base = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return None
    orario = normalize_event_time(event.get("orario"))
    hour, minute = map(int, orario.split(":"))
    return base.replace(hour=hour, minute=minute, tzinfo=tz)


def lead_hours_label(hours: int) -> str:
    if hours == 1:
        return "1 ora prima"
    return f"{hours} ore prima"


async def _reminder_already_sent(db, event_id: str, member_id: str, lead_hours: int) -> bool:
    found = await db.event_reminder_log.find_one(
        {"eventId": event_id, "memberId": member_id, "leadHours": lead_hours},
        {"_id": 1},
    )
    return found is not None


async def _mark_reminder_sent(db, event_id: str, member_id: str, lead_hours: int) -> None:
    await db.event_reminder_log.insert_one(
        {
            "eventId": event_id,
            "memberId": member_id,
            "leadHours": lead_hours,
            "sentAt": datetime.now(timezone.utc).isoformat(),
        }
    )


async def _invited_members_with_email(db, event: dict[str, Any]) -> list[dict]:
    members = await db.members.find(
        {"email": {"$exists": True, "$ne": ""}},
        {"_id": 0, "id": 1, "firstName": 1, "lastName": 1, "email": 1, "emailNotifyEvents": 1, "emailNotifyEventLeadHours": 1},
    ).to_list(2000)
    out: list[dict] = []
    for m in members:
        if not member_invited_to_event(event, m["id"]):
            continue
        if not m.get("emailNotifyEvents"):
            continue
        lead = int(m.get("emailNotifyEventLeadHours") or 24)
        if lead not in EVENT_REMINDER_LEAD_HOURS:
            lead = 24
        m["emailNotifyEventLeadHours"] = lead
        out.append(m)
    return out


async def process_event_reminders(*, now: datetime | None = None) -> dict:
    """Invia promemoria in finestra [target, target+REMINDER_WINDOW)."""
    db = get_db()
    now = (now or datetime.now(ROME)).astimezone(ROME)
    today = now.strftime("%Y-%m-%d")

    events = await db.events.find(
        {"date": {"$gte": today}},
        {"_id": 0},
    ).to_list(500)

    sent = 0
    skipped = 0
    errors = 0

    for event in events:
        start = event_start_datetime(event)
        if not start or start <= now:
            continue

        members = await _invited_members_with_email(db, event)
        if not members:
            continue

        for member in members:
            lead = member["emailNotifyEventLeadHours"]
            target = start - timedelta(hours=lead)
            if not (target <= now < target + REMINDER_WINDOW):
                continue
            if await _reminder_already_sent(db, event["id"], member["id"], lead):
                skipped += 1
                continue

            email = (member.get("email") or "").strip()
            if not email:
                skipped += 1
                continue

            subject = f"Promemoria evento: {event.get('titolo', 'Evento AIA Legnano')}"
            html = render_event_reminder_email(event, member, lead)
            ok = await send_email(email, subject, html)
            if ok:
                await _mark_reminder_sent(db, event["id"], member["id"], lead)
                sent += 1
            else:
                errors += 1
                logger.warning(
                    "Promemoria evento non inviato (mailer): event=%s member=%s lead=%sh",
                    event.get("id"),
                    member.get("id"),
                    lead,
                )

    return {"sent": sent, "skipped": skipped, "errors": errors, "checkedAt": now.isoformat()}


async def notify_event_created(db, event: dict[str, Any]) -> int:
    """Invia email di invito alla creazione dell'evento."""
    members = await _invited_members_with_email(db, event)
    if not members:
        return 0

    link = f"{PORTAL_BASE_URL}/area-associati/calendario"
    sent = 0
    for member in members:
        if await _reminder_already_sent(db, event["id"], member["id"], EVENT_CREATED_LEAD_HOURS):
            continue
        email = (member.get("email") or "").strip()
        if not email:
            continue
        subject = f"Nuovo evento: {event.get('titolo', 'Evento AIA Legnano')}"
        html = render_event_created_email(event, member, link=link)
        if await send_email(email, subject, html):
            await _mark_reminder_sent(db, event["id"], member["id"], EVENT_CREATED_LEAD_HOURS)
            sent += 1
    if sent:
        logger.info("Notifiche creazione evento inviate: %s (event=%s)", sent, event.get("id"))
    return sent


def schedule_event_created_notifications(db, event: dict[str, Any]) -> None:
    """Fire-and-forget dopo creazione evento."""
    asyncio.create_task(notify_event_created(db, event))
