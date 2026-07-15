from app.designation_legnano import section_matches
from app.scrapers.aia_lombardia import parse_des_page
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


class TestSectionMatches:
    def test_legnano_in_section(self):
        assert section_matches("Legnano", "Legnano")
        assert section_matches("Sez. Legnano", "Legnano")

    def test_empty_or_other_section(self):
        assert not section_matches("", "Legnano")
        assert not section_matches("Padova", "Legnano")


class TestScraperFilter:
    def test_empty_section_excluded_when_filtering(self):
        html = (FIXTURES / "des_ecc_a.html").read_text(encoding="utf-8")
        rows = parse_des_page(html, "https://example/des.asp", "3-0-ECC-A")
        filtered = [r for r in rows if section_matches(r.referee_section, "Legnano")]
        assert len(filtered) < len(rows)
