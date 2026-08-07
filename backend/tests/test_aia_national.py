"""Tests for national AIA FIGC designazioni parser."""

from app.scrapers.aia_national import (
    NATIONAL_HUBS,
    parse_dettaglio_page,
    _parse_national_officials,
)

SAMPLE = """
FIORENTINA – ATALANTA Venerdì 22/05 h.20.45 PERRI VOTTA – PRESSATO IV: MASSA VAR: DI BELLO AVAR: SERRA
BOLOGNA – INTER Sabato 23/05 h. 18.00 BONACINA LAGHEZZA – ZEZZA IV: MARCENARO VAR: PEZZUTO AVAR: BARONI
"""


class TestNationalOfficials:
    def test_parse_arbitro_and_assistenti(self):
        roles = dict(
            _parse_national_officials(
                "PERRI VOTTA – PRESSATO IV: MASSA VAR: DI BELLO AVAR: SERRA"
            )
        )
        assert roles["Arbitro"] == "PERRI"
        assert roles["Assistente 1"] == "VOTTA"
        assert roles["Assistente 2"] == "PRESSATO"
        assert roles["IV"] == "MASSA"
        assert roles["VAR"] == "DI BELLO"
        assert roles["AVAR"] == "SERRA"


class TestParseDettaglio:
    def test_parses_two_matches(self):
        from app.scrapers.aia_national import NationalHub

        hub = NationalHub(
            "can",
            "https://www.aia-figc.it/designazioni/can/",
            "dettaglio",
            "aia-figc-can",
            "C.A.N.",
        )
        html = f"<html><body><div id='content'><h1>SERIE A</h1>{SAMPLE}</div></body></html>"
        rows = parse_dettaglio_page(html, "https://x/dettaglio.asp?ID=1", "1", hub)
        assert len(rows) >= 6
        arbitri = [r for r in rows if r.role == "Arbitro"]
        assert any("PERRI" in r.member_name for r in arbitri)
        assert any("FIORENTINA" in (r.match_home or "") for r in rows)
