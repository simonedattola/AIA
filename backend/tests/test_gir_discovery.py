"""Scoperta gironi sezione CRA quando Default.asp non espone link."""

from app.scrapers.aia_lombardia import (
    AiaLombardiaScraper,
    _dedupe_gir_urls,
    _regional_gir_suffixes,
    discover_cra_regional_gir_urls,
    discover_gir_urls_for_section,
)


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


def test_discover_cra_regional_includes_pri():
    hub_html = """
    <a href="gir.asp?gare=3-0-PRI">Prima Categoria</a>
    <a href="gir.asp?gare=3-0-SEC">Seconda</a>
    <a href="gir.asp?gare=3-270-SEC">ignore section</a>
    """

    def fetch_html(_client, url):
        assert url.rstrip("/").endswith("lombardia")
        return hub_html

    found = discover_cra_regional_gir_urls(
        object(),
        "https://www.aia-figc.it/designazioni/lombardia/",
        fetch_html,
    )
    codes = [u.split("gare=")[-1] for u in found]
    assert "3-0-PRI" in codes
    assert "3-0-SEC" in codes
    assert not any(c.startswith("3-270") for c in codes)


def test_legnano_discover_merges_section_and_cra_pri():
    """Sezione 3-270 non elenca PRI; va preso dal CRA 3-0-PRI."""
    section_html = """
    <a href="gir.asp?gare=3-270-SEC">SEC</a>
    <a href="gir.asp?gare=3-270-PRO">PRO</a>
    """
    hub_html = """
    <a href="gir.asp?gare=3-0-PRI">PRI</a>
    <a href="gir.asp?gare=3-0-SEC">SEC</a>
    <a href="gir.asp?gare=3-0-ECC">ECC</a>
    """

    pages = {
        "https://www.aia-figc.it/designazioni/lombardia/default.asp?gare=3-270": section_html,
        "https://www.aia-figc.it/designazioni/lombardia/": hub_html,
        "https://www.aia-figc.it/designazioni/lombardia": hub_html,
    }

    class FakeClient:
        pass

    scraper = AiaLombardiaScraper(
        section_gare="3-270",
        base_url="https://www.aia-figc.it/designazioni/lombardia/",
        request_delay=0,
    )

    def fake_fetch(_client, url):
        for key, html in pages.items():
            if url.rstrip("/") == key.rstrip("/") or url.startswith(key):
                # Exact prefer; default.asp vs hub root
                if "default.asp" in url and "default.asp" not in key:
                    continue
                if "default.asp" in key and "default.asp" not in url:
                    continue
                return html
        if "default.asp" in url:
            return section_html
        return hub_html

    scraper.fetch = fake_fetch  # type: ignore[method-assign]
    found = scraper.discover_gir_urls(FakeClient())
    codes = [u.split("gare=")[-1] for u in found]
    assert "3-270-SEC" in codes
    assert "3-270-PRO" in codes
    assert "3-0-PRI" in codes
    assert "3-0-ECC" in codes


def test_dedupe_gir_strips_translate_params():
    urls = [
        "https://www.aia-figc.it/designazioni/lombardia/gir.asp?gare=3-0-PRI&_x_tr_sl=auto",
        "https://www.aia-figc.it/designazioni/lombardia/gir.asp?gare=3-0-PRI",
    ]
    out = _dedupe_gir_urls(urls)
    assert len(out) == 1
    assert out[0].endswith("gare=3-0-PRI")
    assert "_x_tr_" not in out[0]
