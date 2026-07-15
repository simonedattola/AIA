"""Password portale associati: nome.cognome iniziale."""
from __future__ import annotations


def default_portal_password(first_name: str, last_name: str) -> str:
    def norm(s: str) -> str:
        return (
            (s or "")
            .strip()
            .lower()
            .replace("à", "a")
            .replace("è", "e")
            .replace("é", "e")
            .replace("ì", "i")
            .replace("ò", "o")
            .replace("ù", "u")
        )

    return f"{norm(first_name)}.{norm(last_name)}"


def member_can_use_portal(member: dict) -> bool:
    role = (member.get("memberRole") or member.get("kind") or "").lower()
    if role in ("osservatore",):
        return True
    if role in ("consiglio_direttivo",):
        return True
    if role in ("arbitro", "assistente", "associato"):
        return bool((member.get("meccanografico") or "").strip())
    return bool((member.get("meccanografico") or "").strip())
