"""Filtro sezione arbitrale Legnano per import e visualizzazione designazioni."""
from __future__ import annotations

import re


def normalize_section_filter(section: str | None) -> str:
    return (section or "Legnano").strip()


def section_matches(referee_section: str, section_filter: str | None = None) -> bool:
    """True solo se la sezione contiene il testo richiesto (es. Legnano)."""
    needle = normalize_section_filter(section_filter).lower()
    if not needle:
        return True
    hay = re.sub(r"\s+", " ", (referee_section or "").replace("\ufeff", "")).strip().lower()
    return needle in hay


def mongo_legnano_section_clause(section_filter: str | None = None) -> dict:
    needle = normalize_section_filter(section_filter)
    return {"refereeSection": {"$regex": re.escape(needle), "$options": "i"}}


def mongo_drop_non_legnano_aia_clause(section_filter: str | None = None) -> dict:
    """Per pulizia DB: tutte le import AIA senza Legnano in sezione."""
    legnano = mongo_legnano_section_clause(section_filter)
    return {
        "source": {"$regex": r"^aia-figc"},
        "$nor": [legnano],
    }
