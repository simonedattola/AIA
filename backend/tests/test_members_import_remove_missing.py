from pathlib import Path

import pytest

from app.members_import import parse_members_file, _find_existing_member

FIXTURE = Path(__file__).parent / "fixtures" / "elenco_associati_2026_08_24.xls"


def test_parse_elenco_associati_skips_totali_row():
    rows, warnings, meta = parse_members_file(FIXTURE.read_bytes(), "elenco.xls")
    assert len(rows) == 174
    assert meta["fileType"] == "html-xls"
    assert not any(
        "TOTALI" in f"{r['firstName']} {r['lastName']}".upper() for r in rows
    )
    meccs = [r["meccanografico"] for r in rows if r.get("meccanografico")]
    assert len(meccs) == len(set(meccs))


@pytest.mark.asyncio
async def test_find_existing_keeps_homonyms_distinct():
    """Due omonimi con meccanografici diversi non devono collassare."""

    class Coll:
        async def find_one(self, query, proj=None):
            mec = query.get("meccanografico")
            if mec == "56158447":
                return None
            if mec == "66187522":
                return {
                    "id": "a",
                    "firstName": "LUCA",
                    "lastName": "COLOMBO",
                    "meccanografico": "66187522",
                }
            return None

        def find(self, query, proj=None):
            class C:
                async def to_list(self, n):
                    return [
                        {
                            "id": "a",
                            "firstName": "LUCA",
                            "lastName": "COLOMBO",
                            "meccanografico": "66187522",
                        }
                    ]

            return C()

    class FakeDB:
        members = Coll()

    row = {
        "firstName": "LUCA",
        "lastName": "COLOMBO",
        "meccanografico": "56158447",
        "email": "",
    }
    found = await _find_existing_member(FakeDB(), row)
    assert found is None
