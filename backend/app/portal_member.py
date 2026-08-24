"""Serializzazione associato per API portale (senza password)."""

from __future__ import annotations

from typing import Any

from .person_names import format_person_name_parts


def is_staff_portal(member: dict) -> bool:
    r = (member.get("memberRole") or member.get("kind") or "").lower()
    return r in ("osservatore", "consiglio_direttivo")


def member_public(member: dict) -> dict:
    first, last = format_person_name_parts(
        member.get("firstName"), member.get("lastName")
    )
    return {
        "id": member.get("id"),
        "slug": member.get("slug"),
        "firstName": first or member.get("firstName"),
        "lastName": last or member.get("lastName"),
        "memberRole": member.get("memberRole"),
        "category": member.get("category"),
        "photoUrl": member.get("photoUrl"),
        "bio": member.get("bio"),
        "email": member.get("email") if member.get("emailVisibile") else "",
        "phone": member.get("phone") if member.get("telefonoVisibile") else "",
        "emailVisibile": bool(member.get("emailVisibile")),
        "telefonoVisibile": bool(member.get("telefonoVisibile")),
        "emailNotifyEvents": bool(member.get("emailNotifyEvents")),
        "emailNotifyEventLeadHours": int(member.get("emailNotifyEventLeadHours") or 24),
        "emailNotifyComunicazioni": bool(member.get("emailNotifyComunicazioni")),
        "emailNotifyMessages": bool(member.get("emailNotifyMessages")),
        "hasEmail": bool((member.get("email") or "").strip()),
        "awards": member.get("awards") or [],
        "staffPortal": is_staff_portal(member),
    }
