"""Sync scraped AIA FIGC designations into MongoDB."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

from slugify import slugify

from .db import get_db
from .models import Member, _id
from .designation_legnano import mongo_drop_non_legnano_aia_clause, section_matches
from .scrapers.aia_hub import (
    DESIGNAZIONI_ROOT,
    discover_designazioni_hubs,
    scrape_designazioni_hubs,
    scrape_lombardia_all_sections,
)
from .scrapers.aia_lombardia import _clean_text

logger = logging.getLogger(__name__)

SOURCE_PREFIX = "aia-figc"


def _env_bool(key: str, default: str = "true") -> bool:
    return os.environ.get(key, default).lower() in ("1", "true", "yes", "on")


def _filter_scraped_legnano_only(items: list, section_name: str | None) -> list:
    if not section_name:
        return items
    return [r for r in items if section_matches(r.referee_section, section_name)]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_name(name: str) -> str:
    text = re.sub(r"\s+", " ", (name or "").replace("\ufeff", "")).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def _name_match_keys(full_name: str) -> list[str]:
    """
    Chiavi di matching per Nome Cognome ↔ Cognome Nome.

    Gli export sezione usano spesso «Cognome Nome»; in anagrafica è «Nome Cognome».
    """
    norm = _normalize_name(full_name)
    if not norm:
        return []
    parts = norm.split()
    keys = [norm]
    if len(parts) == 2:
        keys.append(f"{parts[1]} {parts[0]}")
    elif len(parts) == 3:
        a, b, c = parts
        keys.extend(
            [
                f"{c} {a} {b}",  # CognomeComposto Nome → Nome CognomeComposto
                f"{b} {c} {a}",
                f"{c} {b} {a}",
                f"{a} {c} {b}",
            ]
        )
    elif len(parts) > 3:
        keys.append(" ".join(reversed(parts)))
        keys.append(f"{parts[-1]} {' '.join(parts[:-1])}")
        keys.append(f"{' '.join(parts[1:])} {parts[0]}")
    # dedupe preserving order
    return list(dict.fromkeys(keys))


def _split_full_name(full_name: str) -> tuple[str, str]:
    """Nome Cognome → (firstName, lastName). Ultimo token = cognome."""
    parts = re.sub(r"\s+", " ", (full_name or "").strip()).split(" ")
    if len(parts) < 2:
        return parts[0] if parts else "", ""
    return " ".join(parts[:-1]), parts[-1]


def _split_full_name_cognome_nome(full_name: str) -> tuple[str, str]:
    """Cognome Nome → (firstName, lastName). Primo token = cognome."""
    parts = re.sub(r"\s+", " ", (full_name or "").strip()).split(" ")
    if len(parts) < 2:
        return parts[0] if parts else "", ""
    return " ".join(parts[1:]), parts[0]


from .member_roles import is_observer_designation_role


async def _unique_slug(db, first_name: str, last_name: str) -> str:
    base = slugify(f"{first_name}-{last_name}") or "associato"
    slug = base
    i = 1
    while await db.members.find_one({"slug": slug}, {"_id": 0, "id": 1}):
        i += 1
        slug = f"{base}-{i}"
    return slug


async def _build_member_lookup(db) -> dict[str, dict]:
    """Map normalized full name / meccanografico -> {id, slug}."""
    from .member_roles import has_designations, normalize_member

    members = await db.members.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "slug": 1,
            "firstName": 1,
            "lastName": 1,
            "meccanografico": 1,
            "memberRole": 1,
            "kind": 1,
            "role": 1,
        },
    ).to_list(2000)
    lookup: dict[str, dict] = {}
    for m in members:
        normalize_member(m)
        if not has_designations(m.get("memberRole")):
            continue
        info = {
            "id": m["id"],
            "slug": m.get("slug", ""),
            "firstName": m.get("firstName", ""),
            "lastName": m.get("lastName", ""),
        }
        for key in _name_match_keys(
            f"{m.get('firstName', '')} {m.get('lastName', '')}"
        ):
            lookup[key] = info
        mec = (m.get("meccanografico") or "").strip()
        if mec:
            lookup[f"mec:{mec.lower()}"] = info
    return lookup


def _lookup_member_info(
    member_lookup: dict[str, dict], full_name: str
) -> Optional[dict]:
    for key in _name_match_keys(full_name):
        info = member_lookup.get(key)
        if info:
            return info
    return None


async def _resolve_member(
    db,
    full_name: str,
    designation_role: str,
    member_lookup: dict[str, dict],
    *,
    surname_first: bool = False,
) -> tuple[Optional[str], str, bool]:
    """Return (memberId, memberSlug, created). Solo per ruoli arbitrali (non osservatore)."""
    if is_observer_designation_role(designation_role):
        return None, "", False
    if not _normalize_name(full_name):
        return None, "", False

    existing = _lookup_member_info(member_lookup, full_name)
    if existing:
        return existing["id"], existing.get("slug", ""), False

    if surname_first:
        first_name, last_name = _split_full_name_cognome_nome(full_name)
    else:
        first_name, last_name = _split_full_name(full_name)
    if not first_name or not last_name:
        logger.warning("Cannot create member from name: %r", full_name)
        return None, "", False

    from .person_names import format_person_name_parts
    from .member_roles import normalize_member

    # Export AIA / file spesso in TUTTO MAIUSCOLO: salva in title case.
    first_name, last_name = format_person_name_parts(first_name, last_name)

    slug = await _unique_slug(db, first_name, last_name)
    member_id = _id()
    is_assistant = "assistente" in (designation_role or "").lower()
    mrole = "assistente" if is_assistant else "arbitro"
    role_label = "Assistente" if is_assistant else "Arbitro"
    member = Member(
        id=member_id,
        slug=slug,
        firstName=first_name,
        lastName=last_name,
        memberRole=mrole,
        role=role_label,
        kind="associato",
        notes="Creato automaticamente da sync designazioni AIA FIGC",
    )
    doc = member.model_dump()
    normalize_member(doc)
    first_name = doc.get("firstName") or first_name
    last_name = doc.get("lastName") or last_name
    await db.members.insert_one(doc.copy())
    info = {
        "id": member_id,
        "slug": slug,
        "firstName": first_name,
        "lastName": last_name,
    }
    for key in _name_match_keys(f"{first_name} {last_name}"):
        member_lookup[key] = info
    logger.info("Created member %s %s (%s)", first_name, last_name, member_id)
    return member_id, slug, True


async def _backfill_member_links(db) -> int:
    """Persist memberId/memberSlug on designations after sync."""
    from .designation_enrich import enrich_designation, build_member_lookups

    members = await db.members.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "slug": 1,
            "firstName": 1,
            "lastName": 1,
            "memberRole": 1,
            "kind": 1,
            "role": 1,
        },
    ).to_list(2000)
    slug_by_id, member_by_name = build_member_lookups(members, arbitri_only=False)
    fixed = 0
    async for des in db.designations.find({}, {"_id": 0}):
        before_slug = des.get("memberSlug") or ""
        before_mid = des.get("memberId")
        enrich_designation(des, slug_by_id, member_by_name)
        updates = {}
        if des.get("memberId") and des.get("memberId") != before_mid:
            updates["memberId"] = des["memberId"]
        if (des.get("memberSlug") or "") != before_slug:
            updates["memberSlug"] = des.get("memberSlug") or ""
        if updates:
            await db.designations.update_one({"id": des["id"]}, {"$set": updates})
            fixed += 1
    return fixed


@dataclass
class FullScrapeResult:
    items: list = field(default_factory=list)
    pages_fetched: int = 0
    errors: list = field(default_factory=list)
    hubs_crawled: int = 0
    lombardia_scraped: int = 0
    other_hubs_scraped: int = 0
    national_by_hub: dict[str, int] = field(default_factory=dict)


def _source_priority(source: str) -> int:
    if source == "aia-figc-lombardia":
        return 0
    if (source or "").startswith(SOURCE_PREFIX):
        return 1
    return 2


# Stessa gara pubblicata con date sfasate di 1–2 giorni (tipico AIA hub/CRA).
NEAR_DATE_DEDUP_DAYS = 2


def _parse_match_day(value: str | None) -> date | None:
    """Estrae ``date`` da ISO / YYYY-MM-DD, oppure None."""
    raw = (value or "").strip()
    if not raw:
        return None
    day = raw[:10]
    try:
        return date.fromisoformat(day)
    except ValueError:
        return None


def _home_away_role_name(doc: dict) -> tuple[str, str, str, str]:
    home = _normalize_name(doc.get("matchHome") or "")
    away = _normalize_name(doc.get("matchAway") or "")
    if (not home or not away) and doc.get("matchLabel") and " - " in doc["matchLabel"]:
        parts = doc["matchLabel"].split(" - ", 1)
        home = home or _normalize_name(parts[0])
        away = away or _normalize_name(parts[1])
    role = _clean_text(doc.get("role") or "").lower()
    name = _normalize_name(doc.get("memberName") or "")
    return home, away, role, name


def _designation_identity_key(doc: dict) -> str:
    """Chiave senza data: stessa gara/ruolo/arbitro (date possono differire di 1–2 gg)."""
    home, away, role, name = _home_away_role_name(doc)
    return f"{home}|{away}|{role}|{name}"


def _designation_match_key(doc: dict) -> str:
    """Chiave logica per dedup DB (anche con externalId legacy)."""
    md = (doc.get("matchDate") or "")[:10]
    return f"{md}|{_designation_identity_key(doc)}"


def _pick_near_date_keepers(
    items: list,
    *,
    identity_fn,
    date_fn,
    sort_key_fn,
    max_day_delta: int = NEAR_DATE_DEDUP_DAYS,
) -> tuple[list, list]:
    """
    Per ogni identità gara/ruolo/nome, tiene la data più vecchia e scarta
    le altre entro ``max_day_delta`` giorni.
    Ritorna (keepers, duplicates_to_drop).
    """
    by_identity: dict[str, list] = {}
    for item in items:
        by_identity.setdefault(identity_fn(item), []).append(item)

    keepers: list = []
    drop: list = []
    for group in by_identity.values():
        group = sorted(group, key=sort_key_fn)
        kept_dates = []
        for item in group:
            d = date_fn(item)
            if d is None:
                keepers.append(item)
                continue
            if any(abs((d - kd).days) <= max_day_delta for kd in kept_dates):
                drop.append(item)
                continue
            kept_dates.append(d)
            keepers.append(item)
    return keepers, drop


def _dedupe_scraped_rows(rows: list) -> list:
    """Evita duplicati tra hub; collassa anche date ±2gg (tiene la più vecchia)."""
    by_eid: dict[str, object] = {}
    for r in rows:
        eid = r.external_id
        if eid not in by_eid or _source_priority(r.source) < _source_priority(
            by_eid[eid].source
        ):
            by_eid[eid] = r
    collapsed = list(by_eid.values())

    def _ident(r) -> str:
        return _designation_identity_key(
            {
                "matchHome": r.match_home,
                "matchAway": r.match_away,
                "matchLabel": r.match_label,
                "role": r.role,
                "memberName": r.member_name,
            }
        )

    def _sort_key(r):
        d = _parse_match_day(r.match_date) or date.max
        return (d, _source_priority(r.source), r.external_id)

    keepers, _dropped = _pick_near_date_keepers(
        collapsed,
        identity_fn=_ident,
        date_fn=lambda r: _parse_match_day(r.match_date),
        sort_key_fn=_sort_key,
    )
    return keepers


async def _purge_duplicate_designations(db) -> int:
    """Rimuove duplicate AIA: stessa gara/ruolo/nome, anche con data ±2 giorni (tiene la prima)."""
    rows = await db.designations.find(
        {"source": {"$regex": f"^{SOURCE_PREFIX}"}},
        {
            "_id": 0,
            "id": 1,
            "source": 1,
            "externalId": 1,
            "matchDate": 1,
            "matchHome": 1,
            "matchAway": 1,
            "matchLabel": 1,
            "role": 1,
            "memberName": 1,
        },
    ).to_list(20000)

    def _sort_key(r: dict):
        d = _parse_match_day(r.get("matchDate")) or date.max
        return (d, _source_priority(r.get("source", "")), r.get("id", ""))

    _keepers, drop = _pick_near_date_keepers(
        rows,
        identity_fn=_designation_identity_key,
        date_fn=lambda r: _parse_match_day(r.get("matchDate")),
        sort_key_fn=_sort_key,
    )

    removed = 0
    for dup in drop:
        res = await db.designations.delete_one({"id": dup["id"]})
        removed += res.deleted_count
    if removed:
        logger.info(
            "Rimosse %s designazioni duplicate AIA (stessa gara, date entro %sgg)",
            removed,
            NEAR_DATE_DEDUP_DAYS,
        )
    return removed


async def _find_existing_near_date(db, doc_fields: dict) -> Optional[dict]:
    """Trova designazione AIA già presente con stessa gara/ruolo/nome e data ±2gg."""
    target_id = _designation_identity_key(doc_fields)
    target_day = _parse_match_day(doc_fields.get("matchDate"))
    member_name = (doc_fields.get("memberName") or "").strip()
    if not target_id or not target_day or not member_name:
        return None
    home, away, _role, name = _home_away_role_name(doc_fields)
    if not home or not away or not name:
        return None
    candidates = await db.designations.find(
        {
            "source": {"$regex": f"^{SOURCE_PREFIX}"},
            "memberName": {
                "$regex": f"^{re.escape(member_name)}$",
                "$options": "i",
            },
        },
        {
            "_id": 0,
            "id": 1,
            "source": 1,
            "matchDate": 1,
            "matchHome": 1,
            "matchAway": 1,
            "matchLabel": 1,
            "role": 1,
            "memberName": 1,
            "externalId": 1,
        },
    ).to_list(300)
    best = None
    best_day = None
    for cand in candidates:
        if _designation_identity_key(cand) != target_id:
            continue
        cand_day = _parse_match_day(cand.get("matchDate"))
        if cand_day is None:
            continue
        if abs((cand_day - target_day).days) > NEAR_DATE_DEDUP_DAYS:
            continue
        if best is None or cand_day < best_day:
            best = cand
            best_day = cand_day
    return best


# Hub nazionali FIGC (non regionali): designazioni con sezione Legnano su tutti i campionati nazionali.
_DEFAULT_NATIONAL_HUBS = "canc,cand,can5elite,can5,canbs"


def _national_hub_slugs() -> frozenset[str]:
    raw = os.environ.get("DESIGNATIONS_NATIONAL_HUBS", _DEFAULT_NATIONAL_HUBS).strip()
    if not raw or raw.lower() in ("0", "false", "no", "off"):
        return frozenset()
    return frozenset(s.strip().lower() for s in raw.split(",") if s.strip())


def _run_full_scrape(
    section_name: Optional[str],
    max_des_pages: Optional[int],
    crawl_all_hubs: bool,
    section_gare: Optional[str] = None,
) -> FullScrapeResult:
    out = FullScrapeResult()

    lomb = scrape_lombardia_all_sections(
        filter_section=section_name,
        max_des_pages=max_des_pages,
        section_gare=section_gare,
    )
    out.items.extend(lomb.items)
    out.pages_fetched += lomb.pages_fetched
    out.errors.extend(lomb.errors)
    out.lombardia_scraped = len(lomb.items)

    national = _national_hub_slugs()
    if national:
        from .scrapers.aia_national import NATIONAL_HUBS, scrape_national_hubs

        allowed = {h.slug for h in NATIONAL_HUBS if h.slug in national}
        hubs_to_scrape = tuple(h for h in NATIONAL_HUBS if h.slug in allowed)
        nat = scrape_national_hubs(
            filter_section=section_name,
            max_des_pages_per_hub=max_des_pages,
            hubs=hubs_to_scrape,
        )
        out.items.extend(nat.items)
        out.pages_fetched += nat.pages_fetched
        out.errors.extend(nat.errors)
        out.other_hubs_scraped += len(nat.items)
        for row in nat.items:
            slug = (row.source or "").replace("aia-figc-", "")
            out.national_by_hub[slug] = out.national_by_hub.get(slug, 0) + 1
        logger.info(
            "Hub nazionali %s: %d righe Legnano (%s)",
            ",".join(sorted(allowed)),
            len(nat.items),
            ", ".join(f"{k}={v}" for k, v in sorted(out.national_by_hub.items())),
        )

    if crawl_all_hubs:
        hubs = discover_designazioni_hubs()
        out.hubs_crawled = max(0, len(hubs) - 1)
        skip = frozenset({"lombardia"}) | national
        extra = scrape_designazioni_hubs(
            filter_section=section_name,
            max_des_pages_per_hub=max_des_pages,
            skip_slugs=skip,
        )
        out.items.extend(extra.items)
        out.pages_fetched += extra.pages_fetched
        out.errors.extend(extra.errors)
        out.other_hubs_scraped += len(extra.items)

    out.items = _dedupe_scraped_rows(out.items)
    return out


def _to_iso_datetime(date_str: str) -> str:
    if not date_str or date_str == "1970-01-01":
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT12:00:00+00:00")
    if "T" in date_str:
        return date_str
    return f"{date_str}T12:00:00+00:00"


async def sync_from_aia_lombardia(
    section_gare: Optional[str] = None,
    filter_section: Optional[str] = None,
    replace_existing: bool = True,
    max_des_pages: Optional[int] = None,
    trigger: str = "manual",
) -> dict:
    section_name = (
        filter_section
        if filter_section is not None
        else os.environ.get("DESIGNATIONS_FILTER_SECTION", "Legnano")
    )
    if section_name == "":
        section_name = None

    crawl_all_hubs = _env_bool("DESIGNATIONS_CRAWL_ALL_HUBS", "false")
    gare = (
        section_gare
        if section_gare is not None
        else os.environ.get("DESIGNATIONS_LEGNANO_GARE", "3-270")
    )

    scrape: FullScrapeResult = await asyncio.to_thread(
        _run_full_scrape,
        section_name,
        max_des_pages,
        crawl_all_hubs,
        gare,
    )

    db = get_db()
    settings_doc = await db.site_settings.find_one(
        {"id": "site-settings"},
        {"_id": 0, "lastDesignationsSync": 1},
    )
    legnano_label = section_name or "Legnano"
    purge_deleted = 0

    scrape.items = _filter_scraped_legnano_only(scrape.items, section_name)

    if section_name and not scrape.items:
        logger.warning(
            "Sync AIA: nessuna designazione per sezione %s — import e pulizia annullati",
            section_name,
        )
        return {
            "ok": False,
            "error": f"Nessuna designazione trovata per la sezione {section_name}. "
            "Verificare il sito AIA FIGC o riprovare più tardi.",
            "scraped": 0,
            "inserted": 0,
            "updated": 0,
            "removed": 0,
            "pagesFetched": scrape.pages_fetched,
            "errors": scrape.errors[:20],
            "filterSection": section_name,
        }

    purge = await db.designations.delete_many(
        mongo_drop_non_legnano_aia_clause(legnano_label)
    )
    purge_deleted = purge.deleted_count
    if purge_deleted:
        logger.info(
            "Rimosse %s designazioni AIA senza sezione %s", purge_deleted, legnano_label
        )

    member_lookup = await _build_member_lookup(db)
    sync_batch_at = _now()

    inserted = 0
    updated = 0
    skipped_no_date = 0
    members_created = 0
    skipped_observer = 0
    scraped_ids: set[str] = set()
    skipped_not_legnano = 0
    for row in scrape.items:
        if section_name and not section_matches(row.referee_section, section_name):
            skipped_not_legnano += 1
            continue
        if row.match_date == "1970-01-01":
            skipped_no_date += 1

        if is_observer_designation_role(row.role):
            skipped_observer += 1
            continue

        member_id, member_slug, created = await _resolve_member(
            db, row.member_name, row.role, member_lookup
        )
        if created:
            members_created += 1

        from .person_names import format_person_name

        display_name = format_person_name(full=row.member_name)
        if member_id:
            info = _lookup_member_info(member_lookup, row.member_name) or {}
            linked_name = (
                f"{info.get('firstName', '')} {info.get('lastName', '')}".strip()
            )
            if linked_name:
                display_name = format_person_name(full=linked_name)

        scraped_ids.add(row.external_id)
        doc_fields = {
            "matchDate": _to_iso_datetime(row.match_date),
            "championship": row.championship,
            "girone": row.girone or "",
            "matchDay": row.match_day or "",
            "matchHome": row.match_home,
            "matchAway": row.match_away,
            "matchLabel": row.match_label,
            "category": row.championship,
            "role": row.role,
            "memberName": display_name,
            "memberId": member_id,
            "memberSlug": member_slug or "",
            "status": "published",
            "source": row.source,
            "externalId": row.external_id,
            "refereeSection": row.referee_section,
            "gareCode": row.gare_code,
            "syncedAt": sync_batch_at,
            "syncBatchAt": sync_batch_at,
            "lastSeenAt": sync_batch_at,
        }
        existing = await db.designations.find_one(
            {
                "externalId": row.external_id,
                "source": {"$regex": f"^{SOURCE_PREFIX}"},
            },
            {"_id": 0, "id": 1, "source": 1, "matchDate": 1, "externalId": 1},
        )
        if not existing:
            existing = await _find_existing_near_date(db, doc_fields)
        if existing:
            # Conserva la data più vecchia se le due sono entro ±2 giorni.
            existing_day = _parse_match_day(existing.get("matchDate"))
            new_day = _parse_match_day(doc_fields.get("matchDate"))
            if (
                existing_day
                and new_day
                and existing_day <= new_day
                and (new_day - existing_day).days <= NEAR_DATE_DEDUP_DAYS
            ):
                doc_fields = {
                    **doc_fields,
                    "matchDate": existing["matchDate"],
                    "externalId": existing.get("externalId") or row.external_id,
                }
            await db.designations.update_one(
                {"id": existing["id"]}, {"$set": doc_fields}
            )
            updated += 1
        else:
            doc = {"id": _id(), "createdAt": _now(), **doc_fields}
            await db.designations.insert_one(doc)
            inserted += 1

    # Non eliminare designazioni assenti dalla fonte: restano per storico profili e conteggio stagione.
    removed = 0

    duplicates_removed = await _purge_duplicate_designations(db)

    from .designation_filters import (
        designations_before_clause,
        designations_keep_from_day,
    )

    keep_from = designations_keep_from_day()
    stale_clause = designations_before_clause(keep_from)
    stale_before = await db.designations.count_documents(stale_clause)
    stale_res = await db.designations.delete_many(stale_clause)
    stale_removed = int(stale_res.deleted_count)
    if stale_removed:
        logger.info(
            "Rimosse %s designazioni anteriori a %s (trovate %s)",
            stale_removed,
            keep_from,
            stale_before,
        )

    backfilled = await _backfill_member_links(db)

    from .member_category import refresh_arbitri_categories

    categories_updated = await refresh_arbitri_categories(db)

    await db.site_settings.update_one(
        {"id": "site-settings"},
        {
            "$set": {
                "lastDesignationsSync": {
                    "at": sync_batch_at,
                    "batchAt": sync_batch_at,
                    "source": "aia-figc",
                    "designazioniRoot": DESIGNAZIONI_ROOT,
                    "hubsCrawled": scrape.hubs_crawled,
                    "lombardiaScraped": scrape.lombardia_scraped,
                    "otherHubsScraped": scrape.other_hubs_scraped,
                    "nationalScraped": scrape.other_hubs_scraped,
                    "nationalByHub": scrape.national_by_hub,
                    "trigger": trigger,
                    "crawlAllHubs": crawl_all_hubs,
                    "filterSection": section_name,
                    "inserted": inserted,
                    "updated": updated,
                    "removed": removed,
                    "duplicatesRemoved": duplicates_removed,
                    "staleRemoved": stale_removed,
                    "keepFrom": keep_from,
                    "membersCreated": members_created,
                    "membersBackfilled": backfilled,
                    "categoriesUpdated": categories_updated,
                    "pagesFetched": scrape.pages_fetched,
                    "errors": scrape.errors[:20],
                    "nextSyncHours": float(
                        os.environ.get("DESIGNATIONS_SYNC_INTERVAL_HOURS", "6")
                    ),
                }
            }
        },
        upsert=True,
    )

    return {
        "ok": True,
        "inserted": inserted,
        "updated": updated,
        "removed": removed,
        "duplicatesRemoved": duplicates_removed,
        "staleRemoved": stale_removed,
        "keepFrom": keep_from,
        "membersCreated": members_created,
        "membersBackfilled": backfilled,
        "categoriesUpdated": categories_updated,
        "scraped": len(scrape.items),
        "nationalScraped": scrape.other_hubs_scraped,
        "nationalByHub": scrape.national_by_hub,
        "hubsCrawled": scrape.hubs_crawled,
        "lombardiaScraped": scrape.lombardia_scraped,
        "otherHubsScraped": scrape.other_hubs_scraped,
        "pagesFetched": scrape.pages_fetched,
        "errors": scrape.errors,
        "skippedNoDate": skipped_no_date,
        "skippedObserver": skipped_observer,
        "skippedNotLegnano": skipped_not_legnano,
        "purgedNonLegnano": purge_deleted,
        "filterSection": section_name,
        "crawlAllHubs": crawl_all_hubs,
    }
