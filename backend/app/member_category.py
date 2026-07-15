"""Aggiornamento automatico categoria arbitro da storico designazioni."""
from __future__ import annotations

from datetime import datetime, timezone

from .championship_tiers import highest_tier_from_designations
from .designation_queries import member_designations_query
from .member_roles import normalize_member


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def compute_category_for_member(db, member: dict) -> str:
    """Calcola il campionato più alto da designazioni (solo ruolo Arbitro)."""
    normalize_member(member)
    if member.get("memberRole") != "arbitro":
        return (member.get("category") or "").strip()

    query = member_designations_query(member, season=None)
    if not query:
        return (member.get("category") or "").strip()

    rows = await db.designations.find(
        query,
        {"_id": 0, "championship": 1, "category": 1, "role": 1},
    ).to_list(2000)
    return highest_tier_from_designations(rows)


async def refresh_member_category(db, member: dict, *, persist: bool = True) -> str:
    """Imposta member.category al campionato più alto e opzionalmente salva su DB."""
    computed = await compute_category_for_member(db, member)
    if persist and computed and computed != (member.get("category") or "").strip():
        await db.members.update_one(
            {"id": member["id"]},
            {"$set": {"category": computed, "updatedAt": _now()}},
        )
        member["category"] = computed
    elif computed:
        member["category"] = computed
    return computed or (member.get("category") or "").strip()


async def refresh_arbitri_categories(db) -> int:
    """Ricalcola categoria per tutti gli arbitri (post-sync)."""
    from .member_roles import legacy_arbitri_query

    updated = 0
    cursor = db.members.find(legacy_arbitri_query(), {"_id": 0})
    async for doc in cursor:
        normalize_member(doc)
        if doc.get("memberRole") != "arbitro":
            continue
        before = (doc.get("category") or "").strip()
        after = await refresh_member_category(db, doc, persist=True)
        if after and after != before:
            updated += 1
    return updated
