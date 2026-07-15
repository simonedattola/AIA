"""Visibilità eventi e inviti associati."""
from __future__ import annotations

from typing import Any


def event_invited_member_ids(event: dict[str, Any]) -> list[str]:
    invited = event.get("invitedMemberIds")
    if invited is not None:
        return list(invited)
    return list(event.get("relatedMemberIds") or [])


def member_invited_to_event(event: dict[str, Any], member_id: str) -> bool:
    invited = event_invited_member_ids(event)
    if not invited:
        return True
    return member_id in invited


def event_visible_on_public_site(event: dict[str, Any]) -> bool:
    return not bool(event.get("portalOnly"))


def public_events_query(*, upcoming: bool = False, today: str = "", current_season: bool = True) -> dict:
    from .designation_filters import event_date_in_season_clause, merge_mongo_queries

    q: dict[str, Any] = {"portalOnly": {"$ne": True}}
    parts: list[dict | None] = [q]
    if current_season:
        parts.append(event_date_in_season_clause())
    if upcoming and today:
        parts.append({"date": {"$gte": today}})
    return merge_mongo_queries(*parts)
