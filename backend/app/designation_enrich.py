"""Normalize designation documents for API responses."""

from __future__ import annotations

import re

from .designations_sync import _normalize_name, _name_match_keys
from .member_roles import (
    has_designations,
    is_observer_designation_role,
    normalize_member,
)

_GIRONE_RE = re.compile(r"girone\s+([^\s·|,;]+)", re.I)
_GIORNATA_RE = re.compile(r"giornat[a]?\s+([^\s·|,;]+)", re.I)


def _as_str(value) -> str:
    return value.strip() if isinstance(value, str) else ""


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
        home = _as_str(item.get("matchHome"))
        away = _as_str(item.get("matchAway"))
        if home and away:
            item["matchLabel"] = f"{home} - {away}"

    if not _as_str(item.get("championship")):
        parsed = _parse_category_string(_as_str(item.get("category")))
        if parsed["championship"]:
            item["championship"] = parsed["championship"]
    if not _as_str(item.get("girone")):
        parsed = _parse_category_string(_as_str(item.get("category")))
        if parsed["girone"]:
            item["girone"] = parsed["girone"]
    if not _as_str(item.get("matchDay")):
        parsed = _parse_category_string(_as_str(item.get("category")))
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

    if not _as_str(item.get("memberSlug")):
        for key in _name_match_keys(_as_str(item.get("memberName"))):
            m = member_by_name.get(key)
            if m:
                item["memberSlug"] = m.get("slug", "")
                if not item.get("memberId"):
                    item["memberId"] = m.get("id")
                break

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
        for key in _name_match_keys(
            f"{_as_str(m.get('firstName'))} {_as_str(m.get('lastName'))}"
        ):
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

    if not _as_str(item.get("memberSlug")):
        for key in _name_match_keys(_as_str(item.get("name"))):
            m = member_by_name.get(key)
            if m and m.get("slug"):
                item["memberSlug"] = m["slug"]
                if not item.get("memberId"):
                    item["memberId"] = m.get("id")
                break

    if m and not _as_str(item.get("photoUrl")):
        photo = _as_str(m.get("photoUrl"))
        if photo:
            item["photoUrl"] = photo

    return item
