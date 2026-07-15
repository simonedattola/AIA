"""Query designazioni collegate a un profilo membro."""
from __future__ import annotations

import re

from .member_roles import has_designations, normalize_member


def member_designations_query(
    member: dict,
    *,
    include_pending: bool = False,
    season: str | None = None,
) -> dict | None:
    """Filtro MongoDB per lo storico designazioni di un arbitro/assistente."""
    normalize_member(member)
    if not has_designations(member.get("memberRole")):
        return None

    mid = member.get("id")
    slug = (member.get("slug") or "").strip()
    full_name = f"{member.get('firstName', '')} {member.get('lastName', '')}".strip()

    link_clauses: list[dict] = []
    if mid:
        link_clauses.append({"memberId": mid})
    if slug:
        link_clauses.append({"memberSlug": slug})
    if full_name:
        link_clauses.append({"memberName": {"$regex": f"^{re.escape(full_name)}$", "$options": "i"}})

    if not link_clauses:
        return None

    from .designation_filters import match_date_in_season_clause

    status_clause = {"status": {"$in": ["published", "pending_approval"]}} if include_pending else {"status": "published"}
    clauses: list[dict] = [
        status_clause,
        {"role": {"$not": {"$regex": "osservatore", "$options": "i"}}},
        {"$or": link_clauses},
    ]
    season_clause = match_date_in_season_clause(season) if season else None
    if season_clause:
        clauses.append(season_clause)
    return {"$and": clauses}


def upcoming_match_date_clause(ref=None) -> dict:
    """matchDate >= inizio giornata UTC (compatibile con ISO datetime e YYYY-MM-DD)."""
    from .designation_filters import iso_day_start, _utc_today

    day = ref or _utc_today()
    if hasattr(day, "date"):
        day = day.date()
    return {"matchDate": {"$gte": iso_day_start(day)[:10]}}


async def find_next_member_designation(db, member: dict) -> dict | None:
    """Prossima designazione pubblicata dell'associato (data >= oggi)."""
    des_q = member_designations_query(member)
    if not des_q:
        return None
    upcoming_q = {"$and": [des_q, upcoming_match_date_clause()]}
    rows = await db.designations.find(upcoming_q, {"_id": 0}).sort("matchDate", 1).limit(1).to_list(1)
    if not rows:
        return None
    from .designation_enrich import enrich_designation, build_member_lookups
    from .member_roles import legacy_arbitri_query

    item = rows[0]
    members = await db.members.find(legacy_arbitri_query(), {"_id": 0}).to_list(2000)
    slug_by_id, member_by_name = build_member_lookups(members)
    enrich_designation(item, slug_by_id, member_by_name)
    return item
