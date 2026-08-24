"""Ranking campionati per statistiche storico arbitrale."""

from __future__ import annotations

import re
from typing import Iterable

from .championship_tiers import is_womens_championship

# Punteggio più alto = categoria più alta (Under allineato a championship_tiers)
_LEVEL_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"serie\s*a\b", re.I), 100),
    (re.compile(r"serie\s*b\b", re.I), 90),
    (re.compile(r"serie\s*c\b", re.I), 80),
    (re.compile(r"eccellenza", re.I), 70),
    (re.compile(r"promozione", re.I), 60),
    (re.compile(r"prima\s+categoria", re.I), 50),
    (re.compile(r"seconda\s+categoria", re.I), 40),
    (re.compile(r"terza\s+categoria", re.I), 30),
    (re.compile(r"juniores|(?:under|u)\s*1[89]\b", re.I), 26),
    (re.compile(r"allievi|(?:under|u)\s*1[67]\b", re.I), 23),
    (re.compile(r"giovanissimi|(?:under|u)\s*1[0-5]\b|esordienti|pulcini", re.I), 20),
    (re.compile(r"calcio\s+a\s+5|futsal", re.I), 15),
]


def championship_level_score(text: str | None) -> int:
    raw = (text or "").strip()
    if not raw:
        return 0
    # Under / giovanili: non far prevalere «Serie A» dentro «Under 17 Serie A-B»
    if re.search(r"(?:under|u)\s*1[89]\b|juniores", raw, re.I):
        return 26
    if re.search(r"(?:under|u)\s*1[67]\b|allievi", raw, re.I):
        return 23
    if re.search(r"(?:under|u)\s*1[0-5]\b|giovanissimi|esordienti|pulcini", raw, re.I):
        return 20
    best = 5  # testo generico ha punteggio minimo
    for pattern, score in _LEVEL_PATTERNS:
        if pattern.search(raw):
            best = max(best, score)
    return best


def highest_championship_label(items: Iterable[dict]) -> str:
    """Categoria/campionato più alto tra le designazioni (stagione)."""
    best_label = ""
    best_score = -1
    for item in items:
        role = (item.get("role") or "").lower()
        if "osservatore" in role:
            continue
        label = (item.get("championship") or item.get("category") or "").strip()
        if not label or is_womens_championship(label):
            continue
        score = championship_level_score(label)
        if score > best_score or (score == best_score and len(label) > len(best_label)):
            best_score = score
            best_label = label
    return best_label or "—"
