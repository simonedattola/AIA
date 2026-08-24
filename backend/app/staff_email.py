"""Casella sezione per notifiche staff (contatti, candidature, galleria, …)."""

from __future__ import annotations

from typing import Any

from .mailer import notify_email


async def staff_notify_email(db: Any) -> str:
    """
    Email della sezione: preferisce Impostazioni sito (admin), poi NOTIFY_EMAIL, poi default.
    """
    site = ""
    if db is not None:
        doc = await db.site_settings.find_one(
            {"id": "site-settings"}, {"_id": 0, "email": 1}
        )
        site = ((doc or {}).get("email") or "").strip()
    if site:
        return site
    return notify_email()
