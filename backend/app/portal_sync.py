"""Sincronizza un associato Mongo verso l'area riservata Next.js (account portale)."""

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

PORTAL_URL = (os.environ.get("PORTAL_URL") or "http://localhost:3001").rstrip("/")
PORTAL_SYNC_SECRET = os.environ.get("PORTAL_SYNC_SECRET", "")


def _map_role(member_role: str) -> str:
    r = (member_role or "arbitro").lower()
    if r == "consiglio_direttivo":
        return "consiglio_direttivo"
    if r == "osservatore":
        return "osservatore"
    return "arbitro"


async def sync_member_to_portal(member: dict[str, Any]) -> Optional[dict]:
    codice = (member.get("meccanografico") or "").strip()
    if not codice:
        return None
    if not PORTAL_SYNC_SECRET:
        logger.debug("PORTAL_SYNC_SECRET non configurato: skip sync portale")
        return None

    payload = {
        "codiceMeccanografico": codice,
        "nome": member.get("firstName") or "",
        "cognome": member.get("lastName") or "",
        "email": member.get("email") or "",
        "telefono": member.get("phone") or "",
        "categoria": member.get("category") or "",
        "memberRole": _map_role(
            member.get("memberRole") or member.get("kind") or "arbitro"
        ),
        "foto": member.get("photoUrl") or "",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                f"{PORTAL_URL}/api/internal/sync-member",
                json=payload,
                headers={"X-Portal-Sync-Secret": PORTAL_SYNC_SECRET},
            )
            if r.status_code >= 400:
                logger.warning(
                    "Sync portale fallita %s: %s", r.status_code, r.text[:200]
                )
                return None
            return r.json()
    except Exception as e:
        logger.warning("Sync portale non raggiungibile: %s", e)
        return None
