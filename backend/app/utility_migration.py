"""Migrate utility content from legacy WordPress site."""

from __future__ import annotations

import html
import re
import urllib.request
from typing import Any

UTILITY_SECTIONS = {
    "lezioni_tecniche": "Materiale lezioni tecniche",
    "polo": "Informazioni sul polo",
    "link_utili": "Link utili",
}

POLO_BODY_HTML = """
<p>Il <strong>polo atletico sezionale</strong> è il luogo dove gli associati si allenano insieme, sotto la guida del preparatore atletico.</p>
<p>L'attività in gruppo è fortemente consigliata: aiuta a conoscere meglio il proprio corpo, le metodologie di preparazione e a affrontare le gare con maggiore consapevolezza, oltre a rafforzare lo spirito di squadra.</p>
<p>Il materiale delle lezioni tecniche (RTO) è disponibile nella sezione dedicata sopra: ogni incontro RTO ha la propria cartella con presentazioni e documenti.</p>
<p><strong>Referente preparazione atletica:</strong> Gaetano Pignataro<br>
<strong>Orari:</strong> martedì e giovedì, 19:00 – 21:00<br>
<strong>Sede:</strong> Centro Sportivo, Via Pace – Legnano (MI)</p>
""".strip()


def _scrape_table(url: str) -> list[dict[str, str]]:
    page = urllib.request.urlopen(url, timeout=30).read().decode("utf-8", "replace")
    rows = re.findall(r"<tr[^>]*>.*?</tr>", page, re.S | re.I)
    out: list[dict[str, str]] = []
    for row in rows:
        m = re.search(
            r"<td[^>]*>.*?<span[^>]*>\s*([^<]+?)\s*</span>.*?href=[\"']([^\"']+)[\"']",
            row,
            re.S | re.I,
        )
        if not m:
            continue
        title = html.unescape(re.sub(r"\s+", " ", m.group(1)).strip())
        link = html.unescape(m.group(2).strip())
        if title and link:
            out.append({"title": title, "url": link})
    return out


def default_utility_seed() -> dict[str, Any]:
    links: list[dict[str, Any]] = []
    try:
        links = _scrape_table("https://www.aia-legnano.it/web-link/")
    except Exception:
        links = []

    items: list[dict[str, Any]] = []
    for i, row in enumerate(links):
        items.append(
            {
                "section": "link_utili",
                "title": row["title"],
                "description": "",
                "url": row["url"],
                "fileUrl": "",
                "sortOrder": i,
            }
        )
    return {
        "polo": {"bodyHtml": POLO_BODY_HTML},
        "items": items,
    }


async def ensure_utility_polo_content(db) -> None:
    """Aggiorna testo polo e rimuove vecchia immagine mappa."""
    await db.site_settings.update_one(
        {"id": "site-settings"},
        {"$set": {"utilityPolo": {"bodyHtml": POLO_BODY_HTML}}},
        upsert=True,
    )


async def ensure_utility_seed(db=None) -> None:
    """Insert link utili and polo content."""
    from .db import get_db
    from .models import UtilityItem, _id, _now

    if db is None:
        db = get_db()

    await ensure_utility_polo_content(db)
    await migrate_rto_utility_material(db)

    link_count = await db.utility_items.count_documents({"section": "link_utili"})
    if link_count > 0:
        return

    seed = default_utility_seed()
    docs = []
    for row in seed["items"]:
        doc = UtilityItem(**row).model_dump()
        doc["id"] = _id()
        doc["createdAt"] = _now()
        docs.append(doc)
    if docs:
        await db.utility_items.insert_many(docs)


async def migrate_rto_utility_material(db) -> None:
    """Copia allegati evento in utilityMaterial per RTO creati prima della separazione."""
    from .event_categories import RTO_EVENT_TYPE_QUERY

    cursor = db.events.find(
        {
            **RTO_EVENT_TYPE_QUERY,
            "attachments.0": {"$exists": True},
            "$or": [
                {"utilityMaterial": {"$exists": False}},
                {"utilityMaterial": []},
            ],
        },
        {"_id": 0, "id": 1, "attachments": 1},
    )
    async for ev in cursor:
        await db.events.update_one(
            {"id": ev["id"]},
            {"$set": {"utilityMaterial": ev.get("attachments") or []}},
        )
