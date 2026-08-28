"""Gironi hub nazionali CAN: link diretti + categorie default.asp."""

from app.scrapers.aia_lombardia import (
    _discover_gir_urls_from_hub_html,
    _discover_regional_suffixes_from_html,
    _extract_gir_urls_from_html,
)


class TestNationalHubGirDiscovery:
    def test_canc_direct_gir_links(self):
        html = """
        <a href="gir.asp?gare=92-0-UDV">SERIE C</a>
        <a href="gir.asp?gare=92-0-CIL">COPPA ITALIA SERIE C</a>
        """
        base = "https://www.aia-figc.it/designazioni/canc/"
        urls = _extract_gir_urls_from_html(html, base)
        assert len(urls) == 2
        assert any("92-0-UDV" in u for u in urls)
        assert any("92-0-CIL" in u for u in urls)

    def test_cand_category_then_gironi(self):
        hub_html = """
        <a href="default.asp?gare=91-0-CII">COPPA ITALIA SERIE D</a>
        """
        cat_html = """
        <a href="gir.asp?gare=91-0-CII-19">Girone 19</a>
        """

        class FakeClient:
            pass

        fetched: dict[str, str] = {}

        def fetch(_client, url):
            fetched[url] = cat_html
            return cat_html

        base = "https://www.aia-figc.it/designazioni/cand/"
        urls = _discover_gir_urls_from_hub_html(FakeClient(), base, hub_html, fetch)
        assert len(urls) == 1
        assert "91-0-CII-19" in urls[0]
        assert any("default.asp?gare=91-0-CII" in u for u in fetched)

    def test_regional_suffixes_from_raw_html(self):
        html = """
        <a href="gir.asp?gare=3-0-SEC">SEC</a>
        <span>hidden gare=3-0-C5J reference</span>
        """
        suffixes = _discover_regional_suffixes_from_html(html, "3-0")
        assert "SEC" in suffixes
        assert "C5J" in suffixes
