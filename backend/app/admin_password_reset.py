"""Reset password amministratore via email (token monouso)."""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from .db import get_db
from .mailer import portal_frontend_url, render_admin_password_reset_email, send_email
from .security import hash_password

logger = logging.getLogger(__name__)

RESET_TTL_MINUTES = int(os.environ.get("ADMIN_RESET_TTL_MINUTES", "60"))
MIN_PASSWORD_LEN = 8
COOLDOWN_MINUTES = 5


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _admin_reset_link(raw_token: str) -> str:
    base = portal_frontend_url().rstrip("/")
    return f"{base}/amministrazione/reimposta-password?token={raw_token}"


async def request_admin_password_reset(email: str) -> bool:
    """
    Crea token e invia email se l'indirizzo appartiene a un admin.
    Ritorna True se l'email è stata inviata (o avrebbe dovuto esserlo).
    """
    normalized = (email or "").strip().lower()
    if not normalized:
        return False

    db = get_db()
    admin = await db.admin_users.find_one({"email": normalized}, {"_id": 0})
    if not admin:
        logger.info("[admin_reset] Richiesta per email sconosciuta (ignorata)")
        return True

    since = (_now() - timedelta(minutes=COOLDOWN_MINUTES)).isoformat()
    recent = await db.admin_password_resets.find_one(
        {"email": normalized, "createdAt": {"$gte": since}, "usedAt": None},
        {"_id": 0, "id": 1},
    )
    if recent:
        logger.info("[admin_reset] Cooldown attivo per %s", normalized)
        return True

    raw = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw)
    expires = _now() + timedelta(minutes=RESET_TTL_MINUTES)
    doc = {
        "id": secrets.token_hex(16),
        "email": normalized,
        "tokenHash": token_hash,
        "expiresAt": expires.isoformat(),
        "createdAt": _now().isoformat(),
        "usedAt": None,
    }
    await db.admin_password_resets.insert_one(doc)

    link = _admin_reset_link(raw)
    name = admin.get("name") or "Amministratore"
    subject = "Reimposta password — Pannello AIA Legnano"
    html = render_admin_password_reset_email(
        name=name, link=link, ttl_minutes=RESET_TTL_MINUTES
    )
    sent = await send_email(normalized, subject, html)
    if not sent:
        logger.warning("[admin_reset] Email non inviata (Resend non configurato?)")
    return True


async def reset_admin_password(token: str, new_password: str) -> None:
    """Valida token e aggiorna password admin."""
    raw = (token or "").strip()
    pwd = (new_password or "").strip()
    if len(raw) < 20:
        raise ValueError("Token non valido")
    if len(pwd) < MIN_PASSWORD_LEN:
        raise ValueError(f"La password deve avere almeno {MIN_PASSWORD_LEN} caratteri")

    db = get_db()
    token_hash = _hash_token(raw)
    now_iso = _now().isoformat()
    row = await db.admin_password_resets.find_one(
        {"tokenHash": token_hash, "usedAt": None},
        {"_id": 0},
    )
    if not row:
        raise ValueError("Link non valido o già utilizzato")
    if (row.get("expiresAt") or "") < now_iso:
        raise ValueError("Link scaduto: richiedi un nuovo reset")

    email = row["email"]
    admin = await db.admin_users.find_one({"email": email}, {"_id": 0, "id": 1})
    if not admin:
        raise ValueError("Account amministratore non trovato")

    pwd_hash = hash_password(pwd)
    await db.admin_users.update_one(
        {"email": email},
        {"$set": {"passwordHash": pwd_hash}},
    )
    await db.admin_password_resets.update_one(
        {"id": row["id"]},
        {"$set": {"usedAt": now_iso}},
    )
    await db.admin_password_resets.update_many(
        {"email": email, "usedAt": None, "id": {"$ne": row["id"]}},
        {"$set": {"usedAt": now_iso}},
    )
    logger.info("[admin_reset] Password aggiornata per %s", email)
