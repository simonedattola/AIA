"""Scoperta gironi sezione CRA quando Default.asp non espone link."""
from app.scrapers.aia_lombardia import _regional_gir_suffixes, discover_gir_urls_for_section


def test_regional_gir_suffixes():
    urls = [
        "https://www.aia-figc.it/designazioni/lombardia/gir.asp?gare=3-0-SEC",
        "https://www.aia-figc.it/designazioni/lombardia/gir.asp?gare=3-0-C5J",
    ]
    assert _regional_gir_suffixes(urls) == ["SEC", "C5J"]


def test_discover_section_gir_from_templates():
    regional_html = """
    <a href="gir.asp?gare=3-0-SEC">SEC</a>
    <a href="gir.asp?gare=3-0-PRI">PRI</a>
  """
    sec_html = '<a href="des.asp?gare=3-270-SEC-R">R</a>'

    def fetch_html(_client, url):
        if url.endswith("lombardia/"):
            return regional_html
        if "3-270-SEC" in url:
            return sec_html
        return ""

    class FakeClient:
        pass

    found = discover_gir_urls_for_section(
        FakeClient(),
        "https://www.aia-figc.it/designazioni/lombardia/",
        "3-270",
        fetch_html,
    )
    assert len(found) == 1
    assert "3-270-SEC" in found[0]
