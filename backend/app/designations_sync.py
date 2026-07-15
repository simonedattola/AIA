"""Sync scraped AIA FIGC designations into MongoDB."""
from __future__ import annotations

import asyncio
import logging
import os
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
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


def _split_full_name(full_name: str) -> tuple[str, str]:
    parts = re.sub(r"\s+", " ", (full_name or "").strip()).split(" ")
    if len(parts) < 2:
        return parts[0] if parts else "", ""
    return " ".join(parts[:-1]), parts[-1]


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

    members = await db.members.find({}, {"_id": 0, "id": 1, "slug": 1, "firstName": 1, "lastName": 1, "meccanografico": 1, "memberRole": 1, "kind": 1, "role": 1}).to_list(2000)
    lookup: dict[str, dict] = {}
    for m in members:
        normalize_member(m)
        if not has_designations(m.get("memberRole")):
            continue
        info = {"id": m["id"], "slug": m.get("slug", "")}
        key = _normalize_name(f"{m.get('firstName', '')} {m.get('lastName', '')}")
        if key:
            lookup[key] = info
        mec = (m.get("meccanografico") or "").strip()
        if mec:
            lookup[f"mec:{mec.lower()}"] = info
    return lookup


async def _resolve_member(
    db,
    full_name: str,
    designation_role: str,
    member_lookup: dict[str, dict],
) -> tuple[Optional[str], str, bool]:
    """Return (memberId, memberSlug, created). Solo per ruoli arbitrali (non osservatore)."""
    if is_observer_designation_role(designation_role):
        return None, "", False
    key = _normalize_name(full_name)
    if not key:
        return None, "", False

    if key in member_lookup:
        m = member_lookup[key]
        return m["id"], m.get("slug", ""), False

    first_name, last_name = _split_full_name(full_name)
    if not first_name or not last_name:
        logger.warning("Cannot create member from name: %r", full_name)
        return None, "", False

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
    await db.members.insert_one(doc.copy())
    member_lookup[key] = {"id": member_id, "slug": slug}
    logger.info("Created member %s %s (%s)", first_name, last_name, member_id)
    return member_id, slug, True


async def _backfill_member_links(db) -> int:
    """Persist memberId/memberSlug on designations after sync."""
    from .designation_enrich import enrich_designation, build_member_lookups

    members = await db.members.find(
        {},
        {"_id": 0, "id": 1, "slug": 1, "firstName": 1, "lastName": 1, "memberRole": 1, "kind": 1, "role": 1},
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


def _source_priority(source: str) -> int:
    if source == "aia-figc-lombardia":
        return 0
    if (source or "").startswith(SOURCE_PREFIX):
        return 1
    return 2


def _dedupe_scraped_rows(rows: list) -> list:
    """Evita duplicati tra hub (stessa gara/ruolo/nome); preferisce Lombardia."""
    best: dict[str, object] = {}
    for r in rows:
        eid = r.external_id
        if eid not in best or _source_priority(r.source) < _source_priority(best[eid].source):
            best[eid] = r
    return list(best.values())


def _designation_match_key(doc: dict) -> str:
    """Chiave logica per dedup DB (anche con externalId legacy)."""
    md = (doc.get("matchDate") or "")[:10]
    home = _normalize_name(doc.get("matchHome") or "")
    away = _normalize_name(doc.get("matchAway") or "")
    if (not home or not away) and doc.get("matchLabel") and " - " in doc["matchLabel"]:
        parts = doc["matchLabel"].split(" - ", 1)
        home = home or _normalize_name(parts[0])
        away = away or _normalize_name(parts[1])
    role = _clean_text(doc.get("role") or "").lower()
    name = _normalize_name(doc.get("memberName") or "")
    return f"{md}|{home}|{away}|{role}|{name}"


async def _purge_duplicate_designations(db) -> int:
    """Rimuove righe AIA duplicate (stessa gara/data/ruolo/arbitro)."""
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
    ).to_list(5000)
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(_designation_match_key(r), []).append(r)

    removed = 0
    for group in groups.values():
        if len(group) <= 1:
            continue
        group.sort(key=lambda x: (_source_priority(x.get("source", "")), x.get("id", "")))
        for dup in group[1:]:
            res = await db.designations.delete_one({"id": dup["id"]})
            removed += res.deleted_count
    if removed:
        logger.info("Rimosse %s designazioni duplicate AIA", removed)
    return removed


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
) -> FullScrapeResult:
    out = FullScrapeResult()

    lomb = scrape_lombardia_all_sections(
        filter_section=section_name,
        max_des_pages=max_des_pages,
    )
    out.items.extend(lomb.items)
    out.pages_fetched += lomb.pages_fetched
    out.errors.extend(lomb.errors)
    out.lombardia_scraped = len(lomb.items)

    national = _national_hub_slugs()
    if national:
        nat = scrape_designazioni_hubs(
            filter_section=section_name,
            max_des_pages_per_hub=max_des_pages,
            skip_slugs=frozenset({"lombardia"}),
            only_slugs=national,
        )
        out.items.extend(nat.items)
        out.pages_fetched += nat.pages_fetched
        out.errors.extend(nat.errors)
        out.other_hubs_scraped += len(nat.items)
        logger.info("Hub nazionali %s: %d righe Legnano", ",".join(sorted(national)), len(nat.items))

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
    section_name = filter_section if filter_section is not None else os.environ.get("DESIGNATIONS_FILTER_SECTION", "Legnano")
    if section_name == "":
        section_name = None

    crawl_all_hubs = _env_bool("DESIGNATIONS_CRAWL_ALL_HUBS", "false")

    scrape: FullScrapeResult = await asyncio.to_thread(
        _run_full_scrape,
        section_name,
        max_des_pages,
        crawl_all_hubs,
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

    purge = await db.designations.delete_many(mongo_drop_non_legnano_aia_clause(legnano_label))
    purge_deleted = purge.deleted_count
    if purge_deleted:
        logger.info("Rimosse %s designazioni AIA senza sezione %s", purge_deleted, legnano_label)

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
            "memberName": row.member_name,
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
            {"_id": 0, "id": 1, "source": 1},
        )
        if existing:
            await db.designations.update_one({"id": existing["id"]}, {"$set": doc_fields})
            updated += 1
        else:
            doc = {"id": _id(), "createdAt": _now(), **doc_fields}
            await db.designations.insert_one(doc)
            inserted += 1

    # Non eliminare designazioni assenti dalla fonte: restano per storico profili e conteggio stagione.
    removed = 0

    duplicates_removed = await _purge_duplicate_designations(db)

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
                    "trigger": trigger,
                    "crawlAllHubs": crawl_all_hubs,
                    "filterSection": section_name,
                    "inserted": inserted,
                    "updated": updated,
                    "removed": removed,
                    "duplicatesRemoved": duplicates_removed,
                    "membersCreated": members_created,
                    "membersBackfilled": backfilled,
                    "categoriesUpdated": categories_updated,
                    "pagesFetched": scrape.pages_fetched,
                    "errors": scrape.errors[:20],
                    "nextSyncHours": float(os.environ.get("DESIGNATIONS_SYNC_INTERVAL_HOURS", "12")),
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
        "membersCreated": members_created,
        "membersBackfilled": backfilled,
        "categoriesUpdated": categories_updated,
        "scraped": len(scrape.items),
        "nationalScraped": scrape.other_hubs_scraped,
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
