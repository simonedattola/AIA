"""Tipi/categorie evento configurabili dall'admin."""

from __future__ import annotations

from datetime import datetime, timezone

DEFAULT_EVENT_TYPES = [
    "Rto",
    "Riunione",
    "Allenamento",
    "Corso",
    "Sociale",
    "Raduno",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_event_type(name: str) -> str:
    text = " ".join((name or "").split()).strip()
    if not text:
        return ""
    return text[0].upper() + text[1:].lower()


def is_rto_event_type(tipo: str) -> bool:
    return normalize_event_type(tipo).casefold() == "rto"


RTO_EVENT_TYPE_QUERY = {"tipo": {"$regex": "^rto$", "$options": "i"}}


def merge_event_types(*lists: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for lst in lists:
        for raw in lst or []:
            tipo = normalize_event_type(raw)
            if not tipo:
                continue
            key = tipo.casefold()
            if key in seen:
                continue
            seen.add(key)
            out.append(tipo)
    return out


async def get_configured_event_types(db) -> list[str]:
    settings = await db.site_settings.find_one(
        {"id": "site-settings"}, {"_id": 0, "eventTypes": 1}
    )
    stored = (settings or {}).get("eventTypes") or []
    if stored:
        return merge_event_types(stored)
    return list(DEFAULT_EVENT_TYPES)


async def get_admin_event_types(db) -> list[str]:
    configured = await get_configured_event_types(db)
    from_events = await db.events.distinct("tipo")
    return merge_event_types(configured, from_events)


async def save_configured_event_types(db, types: list[str]) -> list[str]:
    merged = merge_event_types(types)
    await db.site_settings.update_one(
        {"id": "site-settings"},
        {"$set": {"eventTypes": merged, "updatedAt": _now()}},
        upsert=True,
    )
    return merged


async def ensure_event_type_exists(db, name: str) -> str:
    tipo = normalize_event_type(name)
    if not tipo:
        return "Riunione"
    configured = await get_configured_event_types(db)
    for existing in configured:
        if existing.casefold() == tipo.casefold():
            return existing
    await save_configured_event_types(db, merge_event_types(configured, [tipo]))
    return tipo


async def add_event_type(db, name: str) -> list[str]:
    tipo = normalize_event_type(name)
    if not tipo:
        raise ValueError("Nome tipo obbligatorio")
    configured = await get_configured_event_types(db)
    return await save_configured_event_types(db, merge_event_types(configured, [tipo]))


async def migrate_event_tipos(db) -> int:
    """Allinea i tipi evento salvati al formato con iniziale maiuscola."""
    events = await db.events.find({}, {"_id": 0, "id": 1, "tipo": 1}).to_list(5000)
    updated = 0
    for ev in events:
        old = (ev.get("tipo") or "").strip()
        new = normalize_event_type(old) or "Riunione"
        if old != new:
            await db.events.update_one({"id": ev["id"]}, {"$set": {"tipo": new}})
            updated += 1
    return updated


async def ensure_event_types_seed(db) -> None:
    await migrate_event_tipos(db)
    settings = await db.site_settings.find_one(
        {"id": "site-settings"}, {"_id": 0, "eventTypes": 1}
    )
    from_events = await db.events.distinct("tipo")
    if not settings:
        return
    stored = settings.get("eventTypes") or []
    merged = merge_event_types(DEFAULT_EVENT_TYPES, stored, from_events)
    if merged != merge_event_types(stored):
        await db.site_settings.update_one(
            {"id": "site-settings"},
            {"$set": {"eventTypes": merged, "updatedAt": _now()}},
        )
