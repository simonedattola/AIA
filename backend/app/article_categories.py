"""Categorie articoli configurabili dall'admin."""
from __future__ import annotations

from datetime import datetime, timezone

DEFAULT_ARTICLE_CATEGORIES = [
    "Vita sezionale",
    "Regolamento",
    "Successi",
    "Corso arbitri",
    "Comunicazioni",
    "Raduni",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_category(name: str) -> str:
    return " ".join((name or "").split()).strip()


def merge_categories(*lists: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for lst in lists:
        for raw in lst or []:
            cat = normalize_category(raw)
            if not cat:
                continue
            key = cat.casefold()
            if key in seen:
                continue
            seen.add(key)
            out.append(cat)
    return out


async def get_configured_categories(db) -> list[str]:
    settings = await db.site_settings.find_one({"id": "site-settings"}, {"_id": 0, "articleCategories": 1})
    stored = (settings or {}).get("articleCategories") or []
    if stored:
        return merge_categories(stored)
    return list(DEFAULT_ARTICLE_CATEGORIES)


async def get_admin_article_categories(db) -> list[str]:
    configured = await get_configured_categories(db)
    from_articles = await db.articles.distinct("category")
    from_gallery = await db.gallery_images.distinct("category")
    return merge_categories(configured, from_articles, from_gallery)


async def get_public_article_categories(db) -> list[str]:
    configured = await get_configured_categories(db)
    used = await db.articles.distinct(
        "category",
        {"status": "published", "portalOnly": {"$ne": True}},
    )
    return merge_categories(configured, used)


async def save_configured_categories(db, categories: list[str]) -> list[str]:
    merged = merge_categories(categories)
    await db.site_settings.update_one(
        {"id": "site-settings"},
        {"$set": {"articleCategories": merged, "updatedAt": _now()}},
        upsert=True,
    )
    return merged


async def ensure_category_exists(db, name: str) -> str:
    cat = normalize_category(name)
    if not cat:
        return ""
    configured = await get_configured_categories(db)
    if any(c.casefold() == cat.casefold() for c in configured):
        return cat
    await save_configured_categories(db, merge_categories(configured, [cat]))
    return cat


async def add_article_category(db, name: str) -> list[str]:
    cat = normalize_category(name)
    if not cat:
        raise ValueError("Nome categoria obbligatorio")
    configured = await get_configured_categories(db)
    return await save_configured_categories(db, merge_categories(configured, [cat]))


async def validate_category_choice(db, name: str) -> str:
    """Accetta solo categorie già configurate o in uso; non ne crea di nuove."""
    cat = normalize_category(name)
    if not cat:
        return ""
    allowed = await get_admin_article_categories(db)
    for existing in allowed:
        if existing.casefold() == cat.casefold():
            return existing
    raise ValueError(f"Categoria non valida: {cat}")


async def validate_member_category_choice(db, name: str) -> str:
    """Categorie selezionabili dagli associati (stesso elenco del sito pubblico)."""
    cat = normalize_category(name)
    if not cat:
        return ""
    allowed = await get_public_article_categories(db)
    for existing in allowed:
        if existing.casefold() == cat.casefold():
            return existing
    raise ValueError(f"Categoria non valida: {cat}")


async def ensure_article_categories_seed(db) -> None:
    """Inizializza o integra le categorie su DB esistenti."""
    settings = await db.site_settings.find_one({"id": "site-settings"}, {"_id": 0, "articleCategories": 1})
    from_articles = await db.articles.distinct("category")
    if not settings:
        return
    stored = settings.get("articleCategories") or []
    merged = merge_categories(DEFAULT_ARTICLE_CATEGORIES, stored, from_articles)
    if merged != merge_categories(stored):
        await db.site_settings.update_one(
            {"id": "site-settings"},
            {"$set": {"articleCategories": merged, "updatedAt": _now()}},
        )
