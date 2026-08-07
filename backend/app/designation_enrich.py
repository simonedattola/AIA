"""Normalize designation documents for API responses."""

from __future__ import annotations

import re

from .designations_sync import _normalize_name
from .member_roles import (
    has_designations,
    is_observer_designation_role,
    normalize_member,
)

_GIRONE_RE = re.compile(r"girone\s+([^\s·|,;]+)", re.I)
_GIORNATA_RE = re.compile(r"giornat[a]?\s+([^\s·|,;]+)", re.I)


def _parse_category_string(category: str) -> dict[str, str]:
    text = (category or "").strip()
    if not text:
        return {"championship": "", "girone": "", "matchDay": ""}
    championship = text.split("·")[0].split("|")[0].strip()
    girone = ""
    giornata = ""
    m_g = _GIRONE_RE.search(text)
    if m_g:
        girone = m_g.group(1).strip()
    m_d = _GIORNATA_RE.search(text)
    if m_d:
        giornata = m_d.group(1).strip()
    return {"championship": championship, "girone": girone, "matchDay": giornata}


def enrich_designation(
    item: dict,
    slug_by_id: dict[str, str],
    member_by_name: dict[str, dict],
) -> dict:
    """Fill display fields and memberSlug for public/admin lists."""
    if not item.get("matchLabel"):
        home = (item.get("matchHome") or "").strip()
        away = (item.get("matchAway") or "").strip()
        if home and away:
            item["matchLabel"] = f"{home} - {away}"

    if not (item.get("championship") or "").strip():
        parsed = _parse_category_string(item.get("category") or "")
        if parsed["championship"]:
            item["championship"] = parsed["championship"]
    if not (item.get("girone") or "").strip():
        parsed = _parse_category_string(item.get("category") or "")
        if parsed["girone"]:
            item["girone"] = parsed["girone"]
    if not (item.get("matchDay") or "").strip():
        parsed = _parse_category_string(item.get("category") or "")
        if parsed["matchDay"]:
            item["matchDay"] = parsed["matchDay"]

    mid = item.get("memberId")
    if mid is not None and mid != "":
        slug = slug_by_id.get(str(mid)) or slug_by_id.get(mid)
        if slug:
            item["memberSlug"] = slug

    if is_observer_designation_role(item.get("role")):
        item["memberSlug"] = ""
        item["memberId"] = None
        return item

    if not (item.get("memberSlug") or "").strip():
        key = _normalize_name(item.get("memberName") or "")
        m = member_by_name.get(key)
        if m:
            item["memberSlug"] = m.get("slug", "")
            if not item.get("memberId"):
                item["memberId"] = m.get("id")

    return item


def build_member_lookups(
    members: list[dict],
    *,
    arbitri_only: bool = True,
) -> tuple[dict[str, str], dict[str, dict]]:
    slug_by_id: dict[str, str] = {}
    member_by_name: dict[str, dict] = {}
    for m in members:
        if arbitri_only:
            normalize_member(m)
            if not has_designations(m.get("memberRole")):
                continue
        mid = m.get("id")
        if mid is not None:
            slug_by_id[str(mid)] = m.get("slug", "")
        key = _normalize_name(f"{m.get('firstName', '')} {m.get('lastName', '')}")
        if key:
            member_by_name[key] = m
    return slug_by_id, member_by_name


def enrich_testimonial(
    item: dict,
    slug_by_id: dict[str, str],
    member_by_name: dict[str, dict],
    member_by_id: dict[str, dict] | None = None,
) -> dict:
    """Collega testimonianza al profilo pubblico via memberId o nome."""
    m: dict | None = None
    mid = item.get("memberId")
    if mid is not None and mid != "":
        slug = slug_by_id.get(str(mid)) or slug_by_id.get(mid)
        if slug:
            item["memberSlug"] = slug
        if member_by_id:
            m = member_by_id.get(str(mid)) or member_by_id.get(mid)

    if not (item.get("memberSlug") or "").strip():
        key = _normalize_name(item.get("name") or "")
        m = member_by_name.get(key)
        if m and m.get("slug"):
            item["memberSlug"] = m["slug"]
            if not item.get("memberId"):
                item["memberId"] = m.get("id")

    if m and not (item.get("photoUrl") or "").strip():
        photo = (m.get("photoUrl") or "").strip()
        if photo:
            item["photoUrl"] = photo

    return item
