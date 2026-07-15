"""Import storico arbitrale — Simone Dattola (schede Sinfonia4You 2024/25 e 2025/26)."""
from __future__ import annotations

import asyncio
import re
import uuid
from datetime import datetime, timezone

from app.db import get_db
from app.member_category import refresh_member_category
from app.member_roles import normalize_member

MEMBER_ID = "690637ee-0bf2-45a0-9ee0-4e89db58209e"
MEMBER_SLUG = "simone-dattola"
MEMBER_NAME = "Simone Dattola"

# att, date DD/MM/YYYY, championship, match_day, home, away
ROWS = [
    ("AA2", "17/05/2026", "SECONDA CATEGORIA (R)", "1 R", "VIRTUS CANTALUPO", "MAZZO 80 A.C. SSD A RL"),
    ("AR", "15/05/2026", "TORNEO LND", "0", "O.SA.F. A.S.D. G.SO.", "FOLGORE LEGNANO"),
    ("AR", "10/05/2026", "TORNEO LND", "0", "REAL VANZAGHES EMANTEGAZZA", "VIRTUS CANTALUPO"),
    ("AR", "08/05/2026", "TORNEO LND", "0", "ASD CITT DI SAMARATE", "VILLAPIZZONE"),
    ("AR", "03/05/2026", "U16 PROVINCIALI C11 MASCHILE (LG)", "1 R", "CALCIO SAN GIORGIO A.S.D.", "CASTANESE A.S.D."),
    ("AA2", "19/04/2026", "CAMP. NAZ. U15 LEGAPRO (A)", "13 R", "ALCIONE MILANO SSD A RL", "OSPITALETTO FRANCIACORTA"),
    ("AR", "18/04/2026", "U15 REGIONALI C11 FEMMINILE (D)", "9 A", "MAZZO 80 SSDRL SQ.C", "RHODENSE"),
    ("AR", "12/04/2026", "TERZA CATEGORIA (B)", "13 R", "DOGO A.S.D.", "DON BOSCO"),
    ("AR", "21/03/2026", "U18 REGIONALE MASCHILE C11 (B)", "11 R", "FOOTBALL CLUB PARABIAGO", "VILLA CORTESE"),
    ("AR", "07/03/2026", "JUNIORES PROVINCIALI (B)", "8 R", "MOCCHETTI S.V.O. A.S.SQ.C", "RESCALDA A.S.D."),
    ("AR", "01/03/2026", "TERZA CATEGORIA (G)", "8 R", "CASOREZZO", "AC NERVIANO ASD"),
    ("AR", "22/02/2026", "U14 REGIONALI C11 MASCHILE (B)", "7 R", "ACCADEMIA BUSTESE", "CALCIO CANEGRATE"),
    ("AR", "21/02/2026", "U16 PROVINCIALI C11 MASCHILE (C)", "6 R", "CASTANESE", "SOCCER BOYS TURBIGO"),
    ("AR", "31/01/2026", "JUNIORES PROVINCIALI (B)", "3 R", "VIGOR ACADEMY SENAGO ASD", "BARBAIANA"),
    ("AR", "25/01/2026", "U17 PROVINCIALI C11 MASCHILE (B)", "2 R", "VIGHIGNOLO", "AURORA MILANO A.S.D."),
    ("AR", "18/01/2026", "U17 PROVINCIALI C11 MASCHILE (B)", "1 R", "MOCCHETTI S.V.O. A.S.D.", "ACCADEMIA CALCIO VITTUONE"),
    ("AR", "11/01/2026", "U16 REGIONALI C11 MASCHILE (B)", "1 R", "ACCADEMIA BUSTESE", "ACCADEMIA VARESINA"),
    ("AR", "14/12/2025", "U17 PROVINCIALI C11 MASCHILE (A)", "13 A", "VELA MESERO", "OSSONA A.S.D."),
    ("AR", "29/11/2025", "JUNIORES PROVINCIALI (B)", "11 A", "VIRTUS CANTALUPO", "BARBAIANA"),
    ("AR", "22/11/2025", "JUNIORES PROVINCIALI (B)", "10 A", "VICTOR RHO", "LEGNARELLO"),
    ("AR", "15/11/2025", "JUNIORES PROVINCIALI (A)", "9 A", "TICINIA ROBECCHETTO", "CALCIO SAN GIORGIO A.S.D."),
    ("AR", "08/11/2025", "U18 REGIONALE MASCHILE C11 (B)", "9 A", "SAN VITTORE OLONA ASD", "GALLARATE CALCIO"),
    ("AR", "26/10/2025", "U17 PROVINCIALI C11 MASCHILE (B)", "6 A", "ORATORIO SAN FRANCESCO", "MOCCHETTI S.V.O. A.S.D."),
    ("AR", "19/10/2025", "U17 PROVINCIALI C11 MASCHILE (A)", "5 A", "LEGNARELLO SSM", "ACCADEMIA BMV"),
    ("AR", "12/10/2025", "U17 REGIONALI C11 MASCHILE (A)", "6 A", "ACADEMY LEGNANO CALCIO", "GAVIRATE CALCIO"),
    ("AR", "04/10/2025", "U17 PROVINCIALI C11 MASCHILE (A)", "3 A", "VIRTUS CANTALUPO", "TICINIA ROBECCHETTO"),
    ("AR", "28/09/2025", "U17 PROVINCIALI C11 MASCHILE (A)", "2 A", "CASOREZZO", "ANTONIANA"),
    ("AR", "20/09/2025", "U17 PROVINCIALI C11 MASCHILE (A)", "1 A", "ORATORIO SAN FRANCESCO", "SOCCER BOYS TURBIGO"),
    ("AR", "14/09/2025", "U15 REGIONALI C11 MASCHILE (A)", "1 A", "CALCIO SAN GIORGIO A.S.D.", "FALOPPIESE OLGIATE RONAGO"),
    ("AR", "07/09/2025", "U17 COPPA REGION. C11 MASCHI LE (09)", "1 A", "VELA MESERO", "ACCADEMIA BUSTESE"),
]

# Stagione 2024/2025
ROWS_2024_25 = [
    ("AR", "18/05/2025", "U17 PROVINCIALI C11 MASCHILE (A)", "17 R", "ACCADEMIA BMV", "CASOREZZO"),
    ("AR", "10/05/2025", "U16 PROVINCIALI C11 MASCHILE (B)", "15 R", "SOCCER BOYS", "ACADEMY LEGNANO CALCIO"),
    ("AR", "27/04/2025", "U16 PROVINCIALI C11 MASCHILE (B)", "13 R", "ACCADEMIA BMV", "LEGNARELLO SSM"),
    ("AR", "30/03/2025", "U17 PROVINCIALI C11 MASCHILE (A)", "11 R", "TICINIA ROBECCHETTO", "CASOREZZO"),
    ("AR", "23/03/2025", "U17 PROVINCIALI C11 MASCHILE (A)", "10 R", "ACCADEMIA INVERUNO", "BARBAIANA"),
    ("AR", "16/03/2025", "U14 REGIONALI C11 MASCHILE (A)", "10 R", "ACADEMY LEGNANO CALCIO", "BESNATESE"),
    ("AR", "09/03/2025", "U16 PROVINCIALI C11 MASCHILE (C)", "7 R", "VELA MESERO", "REAL VANZAGHES EMANTEGAZZA"),
    ("AR", "02/02/2025", "U16 PROVINCIALI C11 MASCHILE (C)", "2 R", "VELA MESERO", "OSSONA A.S.D."),
    ("AR", "26/01/2025", "U16 PROVINCIALI C11 MASCHILE (B)", "1 R", "ACADEMY LEGNANO CALCIO", "AMOR SPORTIVA"),
    ("AR", "15/12/2024", "U15 REGIONALI C11 MASCHILE (A)", "15 A", "CALCIO CANEGRATE", "LOMBARDIA 1 S.R.L.S.D."),
    ("AR", "08/12/2024", "U14 REGIONALI C11 MASCHILE (A)", "14 A", "RHODENSE S.S.D.A.R.L.", "ACADEMY LEGNANO CALCIO"),
    ("AR", "01/12/2024", "U16 PROVINCIALI C11 MASCHILE (C)", "11 A", "VICTOR RHO", "PONTEVECCHIO"),
    ("AR", "17/11/2024", "U15 PROVINCIALI C11 MASCHILE (A)", "9 A", "CALCIO CANEGRATE", "CASTANESE"),
    ("AR", "10/11/2024", "U14 PROVINCIALI C11 MASCHILE (C)", "8 A", "ARDOR A.S.D. SQ.B", "CASOREZZO"),
    ("AR", "03/11/2024", "U15 PROVINCIALI C11 MASCHILE (A)", "7 A", "ORATORIANA VITTUONE", "ORATORIO SAN GAETANO"),
    ("AR", "27/10/2024", "U15 PROVINCIALI C11 MASCHILE (A)", "6 A", "ORATORIO VILLA CORTESE", "ACCADEMIA INVERUNO"),
    ("AR", "20/10/2024", "U15 PROVINCIALI C11 MASCHILE (B)", "5 A", "AIROLDI", "LAINATESE A.S.D."),
    ("AR", "13/10/2024", "U14 PROVINCIALI C11 MASCHILE (E)", "4 A", "OSL CALCIO GARBAGNATE", "CALCIO CANEGRATE"),
    ("AR", "29/09/2024", "U14 PROVINCIALI C11 MASCHILE (D)", "2 A", "LEGNARELLO SSM SQ.B", "TICINIA ROBECCHETTO"),
    ("AR", "22/09/2024", "U14 PROVINCIALI C11 MASCHILE (C)", "1 A", "CALCIO SAN GIORGIO A.S.D.", "FOOTBALL CLUB PARABIAGO"),
]

ALL_ROWS = ROWS + ROWS_2024_25

# Gare rifiutate ma giustificate — non conteggiate nello storico
REFUSED_MATCHES = [
    ("22/12/2024", "ACCADEMIA INVERUNO", "SERENISSIMA 1964"),
    ("09/02/2025", "TICINIA ROBECCHETTO", "ACCADEMIA BMV"),
    ("15/03/2026", "PREGNANESE", "AIROLDI"),
    ("07/12/2025", "VILLA CORTESE", "REAL VANZAGHES EMANTEGAZZA"),
]

_GIRONE_RE = re.compile(r"\s*\(([A-Z0-9]{1,3})\)\s*$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_iso_date(d: str) -> str:
    day, month, year = d.split("/")
    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"


def _role(att: str) -> str:
    if att.upper() == "AA2":
        return "Assistente 2"
    return "Arbitro"


def _split_championship(text: str) -> tuple[str, str]:
    m = _GIRONE_RE.search(text.strip())
    if not m:
        return text.strip(), ""
    girone = m.group(1)
    championship = text[: m.start()].strip()
    return championship, girone


async def main() -> None:
    db = get_db()
    member = await db.members.find_one({"id": MEMBER_ID}, {"_id": 0})
    if not member:
        raise SystemExit(f"Member {MEMBER_ID} not found")

    removed = 0
    for date_it, home, away in REFUSED_MATCHES:
        match_date = _to_iso_date(date_it)
        res = await db.designations.delete_many(
            {
                "memberId": MEMBER_ID,
                "matchDate": {"$regex": f"^{match_date}"},
                "matchHome": home,
                "matchAway": away,
            }
        )
        removed += res.deleted_count

    inserted = 0
    skipped = 0
    for att, date_it, championship_raw, match_day, home, away in ALL_ROWS:
        match_date = _to_iso_date(date_it)
        championship, girone = _split_championship(championship_raw)
        role = _role(att)
        match_label = f"{home} - {away}"

        existing = await db.designations.find_one(
            {
                "memberId": MEMBER_ID,
                "matchDate": {"$regex": f"^{match_date}"},
                "matchHome": home,
                "matchAway": away,
                "role": role,
            },
            {"_id": 0, "id": 1},
        )
        if existing:
            skipped += 1
            continue

        doc = {
            "id": str(uuid.uuid4()),
            "matchDate": match_date,
            "championship": championship,
            "girone": girone,
            "matchDay": match_day,
            "matchHome": home,
            "matchAway": away,
            "matchLabel": match_label,
            "category": championship_raw.strip(),
            "role": role,
            "memberName": MEMBER_NAME,
            "memberId": MEMBER_ID,
            "memberSlug": MEMBER_SLUG,
            "status": "published",
            "source": "manual",
            "refereeSection": "Legnano",
            "createdAt": _now(),
        }
        await db.designations.insert_one(doc)
        inserted += 1

    normalize_member(member)
    category = await refresh_member_category(db, member, persist=True)
    total = await db.designations.count_documents({"memberId": MEMBER_ID})
    print(f"removed={removed} inserted={inserted} skipped={skipped} total={total} category={category!r}")


if __name__ == "__main__":
    asyncio.run(main())
