"""Destinatari e registro letture comunicazioni interne."""
from __future__ import annotations

from .member_roles import MEMBER_ROLES, normalize_member


async def comunicazione_destinatari(db, comm: dict) -> list[dict]:
    """Associati a cui è stata inviata la comunicazione (stesso insieme visibile in portale)."""
    if comm.get("allMembers"):
        member_q = {
            "memberRole": {"$in": list(MEMBER_ROLES)},
            "slug": {"$exists": True, "$ne": ""},
        }
        members = await db.members.find(member_q, {"_id": 0}).sort(
            [("lastName", 1), ("firstName", 1)]
        ).to_list(2000)
    else:
        ids = list(comm.get("memberIds") or [])
        if not ids:
            return []
        members = await db.members.find({"id": {"$in": ids}}, {"_id": 0}).sort(
            [("lastName", 1), ("firstName", 1)]
        ).to_list(500)
    for m in members:
        normalize_member(m)
    return members


async def comunicazione_letture_map(db, comm_id: str, member_ids: list[str]) -> dict[str, str]:
    if not member_ids:
        return {}
    rows = await db.comunicazioni_letture.find(
        {
            "comunicazioneId": comm_id,
            "memberId": {"$in": member_ids},
            "letta": True,
        },
        {"_id": 0, "memberId": 1, "readAt": 1},
    ).to_list(2000)
    return {r["memberId"]: r.get("readAt") or "" for r in rows}


async def comunicazione_letture_report(db, comm: dict) -> dict:
    destinatari = await comunicazione_destinatari(db, comm)
    letture = await comunicazione_letture_map(
        db, comm["id"], [m["id"] for m in destinatari]
    )
    rows = []
    for m in destinatari:
        read_at = letture.get(m["id"])
        rows.append({
            "memberId": m["id"],
            "nome": f"{m.get('firstName', '')} {m.get('lastName', '')}".strip(),
            "meccanografico": m.get("meccanografico", ""),
            "visto": bool(read_at),
            "readAt": read_at or None,
        })
    viste = sum(1 for r in rows if r["visto"])
    return {
        "comunicazione": comm,
        "associati": rows,
        "viste": viste,
        "totale": len(rows),
    }
