"""Filtri calendario (pagina Designazioni) vs storico profilo (per stagione)."""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

from .designation_legnano import mongo_legnano_section_clause

SOURCE_AIA_PREFIX = "aia-figc"


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def iso_day_start(d: date) -> str:
    return f"{d.isoformat()}T00:00:00+00:00"


def iso_day_end(d: date) -> str:
    return f"{d.isoformat()}T23:59:59+00:00"


def season_label_from_iso(match_date: str) -> str:
    """Stagione calcistica: 1 agosto Y – 31 luglio Y+1."""
    raw = (match_date or "")[:10]
    try:
        d = date.fromisoformat(raw)
    except ValueError:
        return ""
    y = d.year
    if d.month >= 8:
        return f"{y}-{str(y + 1)[-2:]}"
    return f"{y - 1}-{str(y)[-2:]}"


def parse_season(season: str) -> tuple[str, str] | None:
    """Es. 2025-26 → intervallo ISO matchDate."""
    m = re.match(r"^(\d{4})-(\d{2,4})$", (season or "").strip())
    if not m:
        return None
    y1 = int(m.group(1))
    y2_part = m.group(2)
    y2 = y1 + 1 if len(y2_part) == 2 else int(y2_part)
    if y2 < y1:
        y2 = y1 + 1
    return iso_day_start(date(y1, 8, 1)), iso_day_end(date(y2, 7, 31))


def current_season_label(ref: date | None = None) -> str:
    return season_label_from_iso(iso_day_start(ref or _utc_today()))


def match_date_in_season_clause(season: str) -> dict | None:
    bounds = parse_season(season)
    if not bounds:
        return None
    start, end = bounds
    return {"matchDate": {"$gte": start, "$lte": end}}


def event_date_in_season_clause(season: str | None = None) -> dict | None:
    """Filtro Mongo per campo evento ``date`` (YYYY-MM-DD) nella stagione calcistica."""
    label = season or current_season_label()
    bounds = parse_season(label)
    if not bounds:
        return None
    start, end = bounds
    return {"date": {"$gte": start[:10], "$lte": end[:10]}}


def iso_datetime_in_season_clause(field: str, season: str | None = None) -> dict | None:
    """Filtro Mongo per timestamp ISO (es. createdAt) nella stagione calcistica."""
    label = season or current_season_label()
    bounds = parse_season(label)
    if not bounds:
        return None
    start, end = bounds
    return {field: {"$gte": start, "$lte": end}}


def merge_mongo_queries(*parts: dict | None) -> dict:
    clauses = [p for p in parts if p]
    if not clauses:
        return {}
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


# Finestra in cui le designazioni AIA possono cambiare tra una sync e l'altra.
SYNC_PRUNE_DAYS_PAST = 21
SYNC_PRUNE_DAYS_FUTURE = 21


def match_date_window_clause(
    *,
    days_past: int,
    days_future: int,
    ref: date | None = None,
) -> dict:
    """Intervallo matchDate (senza filtro source)."""
    today = ref or _utc_today()
    start = today - timedelta(days=days_past)
    end = today + timedelta(days=days_future)
    return {
        "matchDate": {"$gte": iso_day_start(start), "$lte": iso_day_end(end)},
    }


def volatile_sync_prune_clause(ref: date | None = None) -> dict:
    """Solo designazioni recenti/prossime: non cancellare lo storico stagionale in sync."""
    return match_date_window_clause(
        days_past=SYNC_PRUNE_DAYS_PAST,
        days_future=SYNC_PRUNE_DAYS_FUTURE,
        ref=ref,
    )


def manual_recent_window_clause(
    *,
    days_past: int = 7,
    days_future: int = 7,
    ref: date | None = None,
) -> dict:
    today = ref or _utc_today()
    start = today - timedelta(days=days_past)
    end = today + timedelta(days=days_future)
    return {
        "source": "manual",
        "matchDate": {"$gte": iso_day_start(start), "$lte": iso_day_end(end)},
    }


def aia_last_sync_clause(last_sync: dict | None) -> dict | None:
    """Designazioni importate nell'ultima sincronizzazione AIA (solo diagnostica)."""
    if not last_sync:
        return None
    batch_at = (last_sync.get("batchAt") or last_sync.get("at") or "").strip()
    if not batch_at:
        return None
    return {
        "source": {"$regex": f"^{SOURCE_AIA_PREFIX}"},
        "$or": [
            {"syncBatchAt": batch_at},
            {"syncedAt": {"$gte": batch_at}, "syncBatchAt": {"$exists": False}},
        ],
    }


def aia_calendar_window_clause(
    *,
    days_past: int = 7,
    days_future: int = 7,
    section_filter: str | None = "Legnano",
    ref: date | None = None,
) -> dict:
    """
    Calendario pubblico /designazioni: designazioni AIA Legnano con data gara
    nella finestra recente (indipendente dall'ultimo batch di sync).
    """
    window = match_date_window_clause(days_past=days_past, days_future=days_future, ref=ref)
    return {
        "$and": [
            {"source": {"$regex": f"^{SOURCE_AIA_PREFIX}"}},
            mongo_legnano_section_clause(section_filter),
            window,
        ],
    }


def designations_page_query(last_sync: dict | None = None) -> dict:
    """
    Pagina /designazioni (solo prossime/recenti):
    - manuali ±7 giorni
    - import AIA sezione Legnano ±7 giorni (lo storico resta in DB per stats e profili)
    """
    _ = last_sync  # compat API; non filtra più per ultimo batch
    visibility: list[dict] = [
        manual_recent_window_clause(),
        aia_calendar_window_clause(),
    ]
    return {
        "$and": [
            {"status": "published"},
            {"role": {"$not": {"$regex": "osservatore", "$options": "i"}}},
            {"$or": visibility},
        ],
    }


def distinct_seasons_from_dates(iso_dates: list[str]) -> list[str]:
    labels = {season_label_from_iso(d) for d in iso_dates if d}
    labels.discard("")
    return sorted(labels, reverse=True)


def match_fingerprint_from_doc(doc: dict) -> tuple[str, str, str] | None:
    """Chiave univoca partita (data + squadre) per conteggi."""
    md = (doc.get("matchDate") or "")[:10]
    home = (doc.get("matchHome") or "").strip().lower()
    away = (doc.get("matchAway") or "").strip().lower()
    if (not home or not away) and doc.get("matchLabel") and " - " in doc["matchLabel"]:
        parts = doc["matchLabel"].split(" - ", 1)
        home = home or parts[0].strip().lower()
        away = away or parts[1].strip().lower()
    if not md or not home or not away:
        return None
    return md, home, away


def _is_referee_role_row(row: dict) -> bool:
    role = (row.get("role") or "").lower()
    if "osservatore" in role:
        return False
    return role.startswith("arbitro") or "assistente" in role


def published_referee_designations_season_query(
    season: str | None = None,
    section_filter: str | None = "Legnano",
) -> dict:
    """Query Mongo: designazioni pubblicate arbitro/assistente nella stagione calcistica."""
    label = season or current_season_label()
    bounds = parse_season(label)
    if not bounds:
        return {"status": "published", "id": "__none__"}
    start, end = bounds
    base = {
        "status": "published",
        "matchDate": {"$gte": start, "$lte": end},
        "role": {"$not": {"$regex": "osservatore", "$options": "i"}},
        "$or": [
            {"role": {"$regex": r"^arbitro", "$options": "i"}},
            {"role": {"$regex": "assistente", "$options": "i"}},
        ],
    }
    if section_filter:
        return {"$and": [base, mongo_legnano_section_clause(section_filter)]}
    return base


def count_refereed_matches_for_season(
    designation_rows: list[dict],
    season: str | None = None,
) -> int:
    """Partite distinte con almeno un arbitro/assistente nella stagione (1 ago – 31 lug)."""
    label = season or current_season_label()
    bounds = parse_season(label)
    if not bounds:
        return 0
    start, end = bounds
    seen: set[tuple[str, str, str]] = set()
    for row in designation_rows:
        md_raw = row.get("matchDate") or ""
        if not (start <= md_raw <= end):
            continue
        if not _is_referee_role_row(row):
            continue
        fp = match_fingerprint_from_doc(row)
        if fp:
            seen.add(fp)
    return len(seen)


def count_refereed_matches_this_season(designation_rows: list[dict]) -> int:
    return count_refereed_matches_for_season(designation_rows)


