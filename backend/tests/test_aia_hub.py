"""Tests hub discovery designazioni AIA."""
from app.scrapers.aia_hub import (
    DESIGNAZIONI_ROOT,
    discover_designazioni_hubs,
    is_excluded_hub_url,
)
from app.scrapers.aia_lombardia import _discover_section_index_urls, _extract_links


def test_excludes_can_hub():
    assert is_excluded_hub_url("https://www.aia-figc.it/designazioni/can/")
    assert is_excluded_hub_url("https://www.aia-figc.it/designazioni/can")
    assert not is_excluded_hub_url("https://www.aia-figc.it/designazioni/canc/")
    assert not is_excluded_hub_url("https://www.aia-figc.it/designazioni/lombardia/")


def test_discover_hubs_from_fixture_html():
    html = """
    <html><body>
    <a href="/designazioni/lombardia/">Lombardia</a>
    <a href="/designazioni/veneto/">Veneto</a>
    <a href="/designazioni/can/">Serie A</a>
    <a href="/designazioni/canc/">CAN C</a>
    </body></html>
    """
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin

    soup = BeautifulSoup(html, "html.parser")
    hubs = {}
    for a in soup.find_all("a", href=True):
        full = urljoin(DESIGNAZIONI_ROOT, a["href"])
        from app.scrapers.aia_hub import is_excluded_hub_url, _hub_slug_from_url

        if is_excluded_hub_url(full):
            continue
        slug = _hub_slug_from_url(full)
        hubs[slug] = full
    assert "lombardia" in hubs
    assert "veneto" in hubs
    assert "canc" in hubs
    assert "can" not in hubs


def test_section_index_urls_from_lombardia_fixture():
    from pathlib import Path

    html = (Path(__file__).parent / "fixtures" / "lombardia_hub.html")
    if not html.exists():
        return
    text = html.read_text(encoding="utf-8")
    base = "https://www.aia-figc.it/designazioni/lombardia/"
    urls = _discover_section_index_urls(text, base)
    assert any("gare=3-270" in u for u in urls)
