"""Credenziali portale su MongoDB (sostituisce sync verso app Next separata)."""
from __future__ import annotations

import logging
from typing import Any

from .db import get_db
from .portal_password import default_portal_password, member_can_use_portal
from .security import hash_password

logger = logging.getLogger(__name__)


def fictitious_meccanografico_for_member(member: dict[str, Any]) -> str | None:
    """Codice derivato dall'id membro (non è un codice AIA reale)."""
    mid = (member.get("id") or "").strip()
    if not mid:
        return None
    return mid.replace("-", "")[:8].upper()


def is_fictitious_meccanografico(member: dict[str, Any]) -> bool:
    mec = (member.get("meccanografico") or "").strip()
    if not mec:
        return False
    fake = fictitious_meccanografico_for_member(member)
    return bool(fake) and mec.upper() == fake


def is_invalid_meccanografico(member: dict[str, Any]) -> bool:
    """Codici da non usare (fittizi, segnaposto)."""
    mec = (member.get("meccanografico") or "").strip()
    if not mec:
        return False
    if mec.upper() == "A":
        return True
    return is_fictitious_meccanografico(member)


async def purge_fictitious_meccanografici() -> int:
    """Rimuove codici meccanografici non validi (fittizi, segnaposto «A», ecc.)."""
    db = get_db()
    n = 0
    cursor = db.members.find(
        {"meccanografico": {"$exists": True, "$ne": ""}},
        {"_id": 0, "id": 1, "meccanografico": 1},
    )
    async for m in cursor:
        if not is_invalid_meccanografico(m):
            continue
        await db.members.update_one(
            {"id": m["id"]},
            {"$unset": {"meccanografico": "", "passwordHash": ""}},
        )
        n += 1
    if n:
        logger.info("Rimossi %s codici meccanografici fittizi", n)
    return n


async def ensure_member_portal_credentials(member: dict[str, Any]) -> None:
    """Imposta passwordHash se c'è codice meccanografico e manca hash."""
    if not member_can_use_portal(member):
        return
    codice = (member.get("meccanografico") or "").strip()
    if not codice or is_invalid_meccanografico(member):
        return
    if member.get("passwordHash"):
        return
    db = get_db()
    pwd = default_portal_password(member.get("firstName", ""), member.get("lastName", ""))
    hashed = hash_password(pwd)
    await db.members.update_one(
        {"id": member["id"]},
        {"$set": {"passwordHash": hashed}},
    )
    member["passwordHash"] = hashed
    logger.info("Password portale impostata per %s %s", member.get("firstName"), member.get("lastName"))


async def backfill_portal_passwords() -> int:
    """All'avvio: hash per tutti gli associati con meccanografico senza password."""
    db = get_db()
    n = 0
    cursor = db.members.find(
        {"meccanografico": {"$exists": True, "$ne": ""}},
        {"_id": 0},
    )
    async for m in cursor:
        if not (m.get("meccanografico") or "").strip():
            continue
        if is_invalid_meccanografico(m):
            continue
        if m.get("passwordHash"):
            continue
        if not member_can_use_portal(m):
            continue
        pwd = default_portal_password(m.get("firstName", ""), m.get("lastName", ""))
        await db.members.update_one(
            {"id": m["id"]},
            {"$set": {"passwordHash": hash_password(pwd)}},
        )
        n += 1
    if n:
        logger.info("Backfill password portale: %s associati", n)
    return n


async def enable_portal_access_for_directory() -> int:
    """
    Profili in anagrafica con codice meccanografico AIA già impostato:
    password iniziale se mancante.
    """
    from .member_roles import MEMBER_ROLES, normalize_member

    n = 0
    db = get_db()
    async for m in db.members.find({}, {"_id": 0}):
        normalize_member(m)
        if m.get("memberRole") not in MEMBER_ROLES:
            continue
        if not (m.get("slug") or "").strip():
            continue
        if not (m.get("meccanografico") or "").strip():
            continue
        if is_invalid_meccanografico(m):
            continue
        if not m.get("passwordHash"):
            await ensure_member_portal_credentials(m)
            n += 1
    if n:
        logger.info("Accesso portale abilitato per %s associati", n)
    return n
