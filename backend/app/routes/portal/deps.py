"""Shared portal helpers."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException

from ...db import get_db
from ...designation_filters import (
    current_season_label,
    event_date_in_season_clause,
)

PRESENZA_STATI = {"PRESENTE", "ASSENTE", "IN_DUBBIO", "NON_RISPOSTO"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _get_member(db, member_id: str) -> dict:
    m = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not m:
        raise HTTPException(status_code=404, detail="Associato non trovato")
    return m


async def _presenza_map(db, event_id: str) -> dict[str, str]:
    rows = await db.presenze_evento.find({"eventId": event_id}, {"_id": 0}).to_list(5000)
    return {r["memberId"]: r.get("stato", "NON_RISPOSTO") for r in rows}


def _event_date_in_season_clause(season: str) -> dict | None:
    return event_date_in_season_clause(season)


async def _member_season_presenze_stats(db, member_id: str, season: str | None = None) -> dict:
    """Presenze/assenze dell'associato nella stagione calcistica (1 ago – 31 lug)."""
    label = season or current_season_label()
    clause = _event_date_in_season_clause(label)
    if not clause:
        return {"stagione": label, "presenti": 0, "assenti": 0}
    events = await db.events.find(clause, {"_id": 0, "id": 1}).to_list(5000)
    event_ids = [e["id"] for e in events]
    if not event_ids:
        return {"stagione": label, "presenti": 0, "assenti": 0}
    rows = await db.presenze_evento.find(
        {"memberId": member_id, "eventId": {"$in": event_ids}},
        {"_id": 0, "stato": 1},
    ).to_list(5000)
    presenti = sum(1 for r in rows if r.get("stato") == "PRESENTE")
    assenti = sum(1 for r in rows if r.get("stato") == "ASSENTE")
    return {"stagione": label, "presenti": presenti, "assenti": assenti}


def _normalize_presenza_stato(stato: str | None) -> str:
    return (stato or "NON_RISPOSTO").upper()


def _presenza_locked(stato: str) -> bool:
    return _normalize_presenza_stato(stato) in ("PRESENTE", "ASSENTE")


async def _upsert_presenza(db, event_id: str, member_id: str, stato: str, updated_by: str) -> None:
    existing = await db.presenze_evento.find_one(
        {"eventId": event_id, "memberId": member_id},
        {"_id": 0, "id": 1},
    )
    doc = {
        "eventId": event_id,
        "memberId": member_id,
        "stato": stato,
        "updatedAt": _now(),
        "updatedBy": updated_by,
    }
    if existing:
        doc["id"] = existing["id"]
    else:
        doc["id"] = str(uuid.uuid4())
    await db.presenze_evento.update_one(
        {"eventId": event_id, "memberId": member_id},
        {"$set": doc},
        upsert=True,
    )
