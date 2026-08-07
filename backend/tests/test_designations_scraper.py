"""Unit tests for AIA FIGC designazioni scraper (offline HTML fixtures)."""

from pathlib import Path

from app.scrapers.aia_lombardia import (
    parse_des_page,
    _extract_links,
    _parse_match_date_from_h3,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8", errors="replace")


class TestParseDesPage:
    def test_legnano_seconda_categoria_parses_matches(self):
        html = _read("des_legnano_sec_r.html")
        rows = parse_des_page(
            html, "https://example/des.asp?gare=3-270-SEC-R", "3-270-SEC-R"
        )
        assert len(rows) >= 2
        names = {r.member_name for r in rows}
        assert "Lorenzo Menapace" in names
        assert "Anita Costa" in names
        assert all(r.championship == "SECONDA CATEGORIA" for r in rows)
        assert all(r.role == "Arbitro" for r in rows)
        assert rows[0].match_date == "2026-05-17"
        assert "PRO JUVENTUTE ASD" in rows[0].match_label
        # Regression: nominativo must be referee, not away team (td index 1)
        away_names = {"UNION ORATORI CASTELLANZA", "MAZZO 80 A.C. SSD A RL"}
        assert not any(r.member_name in away_names for r in rows)

    def test_eccellenza_parses_arbitro_and_assistenti(self):
        html = _read("des_ecc_a.html")
        rows = parse_des_page(
            html, "https://example/des.asp?gare=3-0-ECC-A", "3-0-ECC-A"
        )
        assert len(rows) >= 6  # 2 matches x 3 roles
        roles = {r.role for r in rows}
        assert "Arbitro" in roles
        assert "Assistente 1" in roles and "Assistente 2" in roles
        arbitri = [r for r in rows if r.role == "Arbitro"]
        assistenti = [r for r in rows if r.role.startswith("Assistente")]
        assert any("Veronica Adenti" in r.member_name for r in arbitri)
        assert len(assistenti) >= 2
        assert not any(r.member_name == "SEDRIANO" for r in rows)

    def test_filter_section_legnano(self):
        html = _read("des_legnano_sec_r.html")
        rows = parse_des_page(html, "https://example/des.asp", "3-270-SEC-R")
        legnano = [r for r in rows if "legnano" in r.referee_section.lower()]
        assert len(legnano) == len(rows)


class TestLinkExtraction:
    def test_gir_page_links_to_des(self):
        html = _read("gir_sec.html")
        links = _extract_links(
            html, "https://www.aia-figc.it/designazioni/lombardia/", "des.asp"
        )
        assert any("des.asp" in u and "3-270-SEC" in u for u in links)


class TestDateParsing:
    def test_parse_h3_date(self):
        iso, girone, giornata = _parse_match_date_from_h3(
            "girone R - giornata 1 - gare  del 17/05/2026"
        )
        assert iso == "2026-05-17"
        assert girone == "R"
        assert giornata == "1"
