"""Blocchi CMS predefiniti per ogni pagina di sistema."""

from __future__ import annotations

import uuid
from typing import Any

from .chi_siamo_content import CHI_SIAMO_BODY_HTML

# Intestazione da campi pagina (eyebrow/heading/summary), non da blocco Hero.
COMPACT_HEADER_SLUGS = frozenset(
    {
        "chi-siamo",
        "designazioni",
        "arbitri",
        "osservatori",
        "news",
        "eventi",
        "contatti",
    }
)

# Non gestite dal CMS admin.
FIXED_LAYOUT_SLUGS = frozenset({"area-associati", "arbitro-profilo"})


def _block(block_type: str, config: dict, enabled: bool = True) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "type": block_type,
        "config": config,
        "enabled": enabled,
    }


def _rich(eyebrow: str, title: str, html: str, background: str = "white") -> dict:
    return _block(
        "rich_text",
        {
            "eyebrow": eyebrow,
            "title": title,
            "html": html,
            "maxWidth": "narrow",
            "background": background,
        },
    )


def default_blocks_for_slug(slug: str, page: dict | None = None) -> list[dict]:
    if slug in FIXED_LAYOUT_SLUGS:
        return []

    page = page or {}
    body_html = (page.get("bodyHtml") or "").strip()

    if slug == "chi-siamo":
        story = body_html or CHI_SIAMO_BODY_HTML
        return [
            _rich("", "", story),
            _block(
                "organigramma",
                {
                    "eyebrow": "Governance",
                    "title": "Organigramma sezionale",
                    "intro": "Le persone che fanno funzionare la Sezione:",
                    "scope": "chi_siamo",
                    "presidentFallback": "",
                },
            ),
        ]

    if slug == "designazioni":
        return [
            _block(
                "designations_table",
                {
                    "eyebrow": "",
                    "title": "",
                    "intro": "",
                    "limit": 300,
                    "searchPlaceholder": "Cerca gara o nominativo…",
                    "defaultRole": "",
                },
            ),
        ]

    if slug == "arbitri":
        return [
            _block(
                "members_grid",
                {
                    "eyebrow": "",
                    "title": "",
                    "intro": "",
                    "limit": 500,
                    "searchPlaceholder": "Cerca per nome…",
                    "defaultRole": "",
                },
            ),
        ]

    if slug == "osservatori":
        return [
            _block(
                "members_grid",
                {
                    "eyebrow": "",
                    "title": "",
                    "intro": "",
                    "limit": 500,
                    "searchPlaceholder": "Cerca per nome…",
                    "defaultRole": "osservatore",
                },
            ),
        ]

    if slug == "news":
        return [
            _block(
                "news_grid",
                {
                    "eyebrow": "",
                    "title": "",
                    "intro": "",
                    "pageSize": 24,
                    "showFilters": True,
                },
            ),
        ]

    if slug == "eventi":
        return [
            _block(
                "events_list",
                {
                    "eyebrow": "Calendario sezionale",
                    "title": "Prossimi eventi",
                    "limit": 3,
                    "upcomingOnly": True,
                    "ctaLabel": "",
                    "ctaHref": "/eventi",
                    "showInstagramWidget": False,
                    "showPresidentCard": False,
                    "showCalendar": True,
                },
            ),
        ]

    if slug == "contatti":
        return [
            _block(
                "contact_section",
                {
                    "eyebrow": "La nostra sede",
                    "title": "Contatti",
                    "infoTitle": "Vieni a trovarci",
                    "intro": "",
                    "formTitle": "Scrivici",
                },
            ),
        ]

    return []
