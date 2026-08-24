"""Scala campionati (dal più alto al più basso) per categoria arbitro."""

from __future__ import annotations

import re
import unicodedata

# Indice più basso = campionato più prestigioso
CHAMPIONSHIP_TIERS: tuple[str, ...] = (
    "Serie A",
    "Serie B",
    "Serie C",
    "Serie D",
    "Eccellenza",
    "Promozione",
    "Prima Categoria",
    "Seconda Categoria",
    "Terza Categoria",
    "Juniores",
    "Allievi",
    "Giovanissimi",
)

_TIER_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Serie A", re.compile(r"\bserie\s*a\b", re.I)),
    ("Serie B", re.compile(r"\bserie\s*b\b", re.I)),
    ("Serie C", re.compile(r"\bserie\s*c\b", re.I)),
    ("Serie D", re.compile(r"\bserie\s*d\b", re.I)),
    ("Eccellenza", re.compile(r"\beccellenza\b", re.I)),
    ("Promozione", re.compile(r"\bpromozione\b", re.I)),
    ("Prima Categoria", re.compile(r"\bprima\s+categ", re.I)),
    ("Seconda Categoria", re.compile(r"\bseconda\s+categ", re.I)),
    ("Terza Categoria", re.compile(r"\bterza\s+categ", re.I)),
    ("Juniores", re.compile(r"\bjuniores\b", re.I)),
    ("Allievi", re.compile(r"\ballievi\b", re.I)),
    ("Giovanissimi", re.compile(r"\bgiovanissimi\b", re.I)),
]


def _normalize_text(text: str) -> str:
    t = unicodedata.normalize("NFKD", (text or ""))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().lower()


_WOMENS_CHAMPIONSHIP_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bfemminil", re.I),
    re.compile(r"\bfemm\.?\b", re.I),
    re.compile(r"\bdonne\b", re.I),
    re.compile(r"\bfemale\b", re.I),
    re.compile(r"\bwomen\b", re.I),
    re.compile(r"\bragazze\b", re.I),
    re.compile(r"\bu\d{1,2}f\b", re.I),
)


def is_womens_championship(championship: str | None) -> bool:
    """True se il testo indica un campionato calcistico femminile."""
    from .championship_codes import expand_championship_label

    raw = expand_championship_label(championship)
    if not raw:
        return False
    norm = _normalize_text(raw)
    return any(p.search(norm) for p in _WOMENS_CHAMPIONSHIP_PATTERNS)


def detect_championship_tier(championship: str) -> str | None:
    """Riconosce il livello campionato da testo championship/category (anche sigle)."""
    from .championship_codes import expand_championship_label

    if not (championship or "").strip():
        return None
    expanded = expand_championship_label(championship)
    norm = _normalize_text(expanded)
    for label, pattern in _TIER_PATTERNS:
        if pattern.search(norm):
            return label
    return None


def tier_rank(tier: str) -> int:
    try:
        return CHAMPIONSHIP_TIERS.index(tier)
    except ValueError:
        return len(CHAMPIONSHIP_TIERS)


def is_arbitro_designation_role(role: str | None) -> bool:
    """Solo designazioni come arbitro di gara (esclusi assistenti e osservatori)."""
    r = (role or "").strip().lower()
    if not r or "assistente" in r or "osservatore" in r:
        return False
    return r == "arbitro"


def highest_tier_from_designations(designations: list[dict]) -> str:
    """Campionato più alto arbitrato come Arbitro (esclusi campionati femminili)."""
    best_rank = len(CHAMPIONSHIP_TIERS)
    best_label = ""
    for d in designations:
        if not is_arbitro_designation_role(d.get("role")):
            continue
        raw = (d.get("championship") or d.get("category") or "").strip()
        if is_womens_championship(raw):
            continue
        tier = detect_championship_tier(raw)
        if not tier:
            continue
        rank = tier_rank(tier)
        if rank < best_rank:
            best_rank = rank
            best_label = tier
    return best_label
