"""Sezioni/categorie documenti configurabili dall'admin."""

from __future__ import annotations

from datetime import datetime, timezone

DEFAULT_DOCUMENT_SECTIONS = [
    "Regolamenti del giuoco del calcio",
    "Regolamenti A.I.A.",
    "Documentazione amministrativa CRA/CPA",
    "Documentazione amministrativa Sezioni",
    "Assemblea Sezionale Elettiva",
    "Assemblea Sezionale Ordinaria",
    "Assemblea Regionale Elettiva",
    "Assemblea Generale Elettiva",
]

# Compatibilità DB legacy
LEGACY_CATEGORY_MAP: dict[str, str] = {
    "regolamento": "Regolamenti del giuoco del calcio",
    "modulistica": "Documentazione amministrativa Sezioni",
    "tecnica": "Documentazione amministrativa Sezioni",
    "comunicazioni": "Documentazione amministrativa CRA/CPA",
    "Download sezionale": "Documentazione amministrativa Sezioni",
}

DOCUMENT_SECTIONS = tuple(DEFAULT_DOCUMENT_SECTIONS)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_section_name(name: str) -> str:
    return " ".join((name or "").split()).strip()


def merge_sections(*lists: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for lst in lists:
        for raw in lst or []:
            sec = normalize_section_name(raw)
            if not sec:
                continue
            key = sec.casefold()
            if key in seen:
                continue
            seen.add(key)
            out.append(sec)
    return out


async def get_configured_sections(db) -> list[str]:
    settings = await db.site_settings.find_one(
        {"id": "site-settings"}, {"_id": 0, "documentSections": 1}
    )
    stored = (settings or {}).get("documentSections") or []
    if stored:
        return merge_sections(stored)
    return list(DEFAULT_DOCUMENT_SECTIONS)


async def get_admin_document_sections(db) -> list[str]:
    configured = await get_configured_sections(db)
    from_docs = await db.documents.distinct("category")
    from_section = await db.documents.distinct("section")
    return merge_sections(configured, from_docs, from_section)


async def get_public_document_sections(db) -> list[str]:
    configured = await get_configured_sections(db)
    used = await db.documents.distinct("category")
    return merge_sections(configured, used)


async def save_configured_sections(db, sections: list[str]) -> list[str]:
    merged = merge_sections(sections)
    await db.site_settings.update_one(
        {"id": "site-settings"},
        {"$set": {"documentSections": merged, "updatedAt": _now()}},
        upsert=True,
    )
    return merged


async def add_document_section(db, name: str) -> list[str]:
    sec = normalize_section_name(name)
    if not sec:
        raise ValueError("Nome sezione obbligatorio")
    configured = await get_configured_sections(db)
    return await save_configured_sections(db, merge_sections(configured, [sec]))


async def ensure_section_exists(db, name: str) -> str:
    sec = normalize_section_name(name)
    if not sec:
        return ""
    configured = await get_configured_sections(db)
    if any(s.casefold() == sec.casefold() for s in configured):
        return sec
    await save_configured_sections(db, merge_sections(configured, [sec]))
    return sec


async def normalize_document_category(
    db,
    category: str | None,
    section: str | None = None,
) -> str:
    cat = normalize_section_name(category or "")
    sec = normalize_section_name(section or "")
    configured = await get_configured_sections(db)

    for value in (cat, sec):
        if not value:
            continue
        if value in configured or any(
            s.casefold() == value.casefold() for s in configured
        ):
            return value
        if value in LEGACY_CATEGORY_MAP:
            return LEGACY_CATEGORY_MAP[value]

    if cat:
        return cat
    if sec:
        return sec
    return configured[3] if len(configured) > 3 else DEFAULT_DOCUMENT_SECTIONS[3]


async def ensure_document_sections_seed(db) -> None:
    settings = await db.site_settings.find_one(
        {"id": "site-settings"}, {"_id": 0, "documentSections": 1}
    )
    from_docs = await db.documents.distinct("category")
    if not settings:
        return
    stored = settings.get("documentSections") or []
    merged = merge_sections(DEFAULT_DOCUMENT_SECTIONS, stored, from_docs)
    if merged != merge_sections(stored):
        await db.site_settings.update_one(
            {"id": "site-settings"},
            {"$set": {"documentSections": merged, "updatedAt": _now()}},
        )


async def migrate_legacy_document_categories(db) -> int:
    updated = 0
    for old, new in LEGACY_CATEGORY_MAP.items():
        res = await db.documents.update_many(
            {"$or": [{"category": old}, {"section": old}]},
            {"$set": {"category": new, "section": new}},
        )
        updated += res.modified_count
    configured = await get_configured_sections(db)
    for section in configured:
        res = await db.documents.update_many(
            {"category": section, "section": {"$ne": section}},
            {"$set": {"section": section}},
        )
        updated += res.modified_count
    return updated
