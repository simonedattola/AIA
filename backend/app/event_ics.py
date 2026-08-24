"""Export eventi in formato iCalendar (.ics) e link Google Calendar."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote, urlencode
from zoneinfo import ZoneInfo

ROME = ZoneInfo("Europe/Rome")
DEFAULT_EVENT_TIME = "09:00"
DEFAULT_DURATION = timedelta(hours=2)
ICS_PROD_ID = "-//AIA Legnano//Eventi//IT"


def _normalize_event_time(value: str | None) -> str:
    text = (value or "").strip()
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", text)
    if not m:
        return DEFAULT_EVENT_TIME
    hour, minute = int(m.group(1)), int(m.group(2))
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return f"{hour:02d}:{minute:02d}"
    return DEFAULT_EVENT_TIME


def _event_start(event: dict[str, Any], *, tz: ZoneInfo = ROME) -> datetime | None:
    date = (event.get("date") or "")[:10]
    if not date or len(date) < 10:
        return None
    try:
        base = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return None
    orario = _normalize_event_time(event.get("orario"))
    hour, minute = map(int, orario.split(":"))
    return base.replace(hour=hour, minute=minute, tzinfo=tz)


def _fold_ics_line(line: str) -> str:
    if len(line) <= 75:
        return line
    parts = [line[:75]]
    rest = line[75:]
    while rest:
        parts.append(" " + rest[:74])
        rest = rest[74:]
    return "\r\n".join(parts)


def _ics_escape(text: str) -> str:
    return (
        (text or "")
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "\\n")
    )


def _ics_dt(dt: datetime) -> str:
    local = dt.astimezone(ROME)
    return local.strftime("%Y%m%dT%H%M%S")


def event_end_datetime(
    event: dict[str, Any], *, duration: timedelta = DEFAULT_DURATION
) -> datetime | None:
    start = _event_start(event)
    if not start:
        return None
    orario_fine = (event.get("orarioFine") or "").strip()
    if orario_fine:
        fine = _normalize_event_time(orario_fine)
        hour, minute = map(int, fine.split(":"))
        end = start.replace(hour=hour, minute=minute)
        if end <= start:
            end = end + timedelta(days=1)
        return end
    return start + duration


def ics_uid(event: dict[str, Any]) -> str:
    eid = (event.get("id") or "evento").strip() or "evento"
    return f"aia-legnano-event-{eid}@aia-legnano.it"


def ics_filename(event: dict[str, Any]) -> str:
    title = re.sub(
        r"[^\w\-]+", "-", (event.get("titolo") or "evento").strip(), flags=re.UNICODE
    )
    title = re.sub(r"-{2,}", "-", title).strip("-")[:40] or "evento"
    date = (event.get("date") or "")[:10].replace("-", "")
    return f"aia-legnano-{title}-{date or 'data'}.ics"


def build_ics(
    event: dict[str, Any], *, duration: timedelta = DEFAULT_DURATION
) -> str | None:
    start = _event_start(event)
    end = event_end_datetime(event, duration=duration)
    if not start or not end:
        return None

    titolo = (event.get("titolo") or "Evento AIA Legnano").strip()
    luogo = (event.get("luogo") or "").strip()
    descrizione = (event.get("descrizione") or "").strip()
    now = datetime.now(tz=ZoneInfo("UTC"))

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{ICS_PROD_ID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{ics_uid(event)}",
        f"DTSTAMP:{now.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART;TZID=Europe/Rome:{_ics_dt(start)}",
        f"DTEND;TZID=Europe/Rome:{_ics_dt(end)}",
        f"SUMMARY:{_ics_escape(titolo)}",
    ]
    if luogo:
        lines.append(f"LOCATION:{_ics_escape(luogo)}")
    if descrizione:
        lines.append(f"DESCRIPTION:{_ics_escape(descrizione)}")
    lines.extend(
        [
            "STATUS:CONFIRMED",
            "END:VEVENT",
            "END:VCALENDAR",
        ]
    )
    return "\r\n".join(_fold_ics_line(line) for line in lines) + "\r\n"


def google_calendar_url(
    event: dict[str, Any], *, duration: timedelta = DEFAULT_DURATION
) -> str | None:
    start = _event_start(event)
    end = event_end_datetime(event, duration=duration)
    if not start or not end:
        return None

    start_utc = start.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    end_utc = end.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    params = {
        "action": "TEMPLATE",
        "text": (event.get("titolo") or "Evento AIA Legnano").strip(),
        "dates": f"{start_utc}/{end_utc}",
        "details": (event.get("descrizione") or "").strip(),
        "location": (event.get("luogo") or "").strip(),
        "ctz": "Europe/Rome",
    }
    clean = {
        k: v for k, v in params.items() if v or k in ("action", "text", "dates", "ctz")
    }
    return "https://calendar.google.com/calendar/render?" + urlencode(
        clean, quote_via=quote
    )
