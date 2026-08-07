"""Compat: re-export da member_roles."""

from .member_roles import (
    arbitri_query,
    chi_siamo_query,
    has_designations,
    is_observer_designation_role,
    legacy_arbitri_query,
    legacy_chi_siamo_query,
    normalize_member,
    public_member,
)

# alias storici
associati_query = legacy_arbitri_query
observers_query = legacy_chi_siamo_query


def is_associato_kind(kind: str | None) -> bool:
    return (kind or "associato") in ("associato", "tutor")


def is_observer_kind(kind: str | None) -> bool:
    return (kind or "").lower() in ("oa", "ot", "osservatore")
