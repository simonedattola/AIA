"""Visibilità eventi e inviti associati."""

from __future__ import annotations

from typing import Any

from .member_roles import (
    MEMBER_ROLES,
    member_matches_any_role_group,
    normalize_role_groups,
    role_groups_member_query,
)


def event_invited_member_ids(event: dict[str, Any]) -> list[str]:
    invited = event.get("invitedMemberIds")
    if invited is not None:
        return list(invited)
    return list(event.get("relatedMemberIds") or [])


def event_invited_role_groups(event: dict[str, Any]) -> list[str]:
    return normalize_role_groups(event.get("invitedRoleGroups"))


def event_has_invite_restrictions(event: dict[str, Any]) -> bool:
    return bool(event_invited_member_ids(event) or event_invited_role_groups(event))


def member_invited_to_event(
    event: dict[str, Any],
    member_id: str,
    *,
    member: dict[str, Any] | None = None,
) -> bool:
    invited = event_invited_member_ids(event)
    role_groups = event_invited_role_groups(event)
    if not invited and not role_groups:
        return True
    if invited and member_id in invited:
        return True
    if role_groups and member is not None:
        return member_matches_any_role_group(member, role_groups)
    return False


def event_invited_members_query(event: dict[str, Any]) -> dict[str, Any]:
    """Query MongoDB per l'elenco associati invitati (presenze, email, …)."""
    invited = event_invited_member_ids(event)
    role_groups = event_invited_role_groups(event)
    if invited:
        return {
            "memberRole": {"$in": list(MEMBER_ROLES)},
            "slug": {"$exists": True, "$ne": ""},
            "id": {"$in": invited},
        }
    if role_groups:
        return role_groups_member_query(role_groups)
    return {
        "memberRole": {"$in": list(MEMBER_ROLES)},
        "slug": {"$exists": True, "$ne": ""},
    }


def event_visible_on_public_site(event: dict[str, Any]) -> bool:
    return not bool(event.get("portalOnly"))


def public_events_query(
    *, upcoming: bool = False, today: str = "", current_season: bool = True
) -> dict:
    from .designation_filters import event_date_in_season_clause, merge_mongo_queries

    q: dict[str, Any] = {"portalOnly": {"$ne": True}}
    parts: list[dict | None] = [q]
    if current_season:
        parts.append(event_date_in_season_clause())
    if upcoming and today:
        parts.append({"date": {"$gte": today}})
    return merge_mongo_queries(*parts)
