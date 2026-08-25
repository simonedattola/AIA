"""Sitemap e robots.txt dinamici."""

import pytest

from app.sitemap import (
    absolute_url,
    render_robots_txt,
    render_sitemap_xml,
    _iso_date,
)


def test_iso_date_normalizes():
    assert _iso_date("2026-08-24T10:00:00Z") == "2026-08-24"
    assert _iso_date("2026-08-24") == "2026-08-24"
    assert _iso_date("") is None
    assert _iso_date(None) is None


def test_absolute_url(monkeypatch):
    monkeypatch.setenv("PORTAL_FRONTEND_URL", "https://www.aia-legnano.it")
    assert absolute_url("/") == "https://www.aia-legnano.it/"
    assert absolute_url("/news/foo") == "https://www.aia-legnano.it/news/foo"


def test_render_sitemap_xml_structure():
    xml = render_sitemap_xml(
        [
            {
                "loc": "https://www.aia-legnano.it/",
                "lastmod": "2026-08-24",
                "changefreq": "daily",
                "priority": "1.0",
            },
            {
                "loc": "https://www.aia-legnano.it/news/test-articolo",
                "lastmod": "2026-08-20",
                "changefreq": "weekly",
                "priority": "0.7",
            },
        ]
    )
    assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"' in xml
    assert "<loc>https://www.aia-legnano.it/</loc>" in xml
    assert "<loc>https://www.aia-legnano.it/news/test-articolo</loc>" in xml
    assert "<priority>1.0</priority>" in xml


def test_render_robots_txt(monkeypatch):
    monkeypatch.setenv("PORTAL_FRONTEND_URL", "https://www.aia-legnano.it")
    txt = render_robots_txt()
    assert "User-agent: *" in txt
    assert "Disallow: /amministrazione" in txt
    assert "Disallow: /area-associati" in txt
    assert "Sitemap: https://www.aia-legnano.it/sitemap.xml" in txt


class _FakeCursor:
    def __init__(self, items):
        self._items = items

    async def to_list(self, n):
        return self._items[:n]


class _FakeColl:
    def __init__(self, items):
        self._items = items

    def find(self, query, projection=None):
        return _FakeCursor(self._items)


class _FakeDb:
    def __init__(self):
        self.pages = _FakeColl(
            [
                {"slug": "home", "updatedAt": "2026-08-01T00:00:00Z"},
                {"slug": "pagina-custom", "updatedAt": "2026-08-10T00:00:00Z"},
                {"slug": "area-associati", "updatedAt": "2026-08-01T00:00:00Z"},
            ]
        )
        self.articles = _FakeColl(
            [
                {
                    "slug": "vittoria-regionale",
                    "updatedAt": "2026-08-15T12:00:00Z",
                    "publishedAt": "2026-08-14T12:00:00Z",
                }
            ]
        )
        self.members = _FakeColl(
            [
                {"slug": "mario-rossi", "updatedAt": "2026-07-01T00:00:00Z"},
                {"slug": ""},
            ]
        )


@pytest.mark.asyncio
async def test_collect_sitemap_urls(monkeypatch):
    from app.sitemap import collect_sitemap_urls

    monkeypatch.setenv("PORTAL_FRONTEND_URL", "https://www.aia-legnano.it")
    urls = await collect_sitemap_urls(_FakeDb())
    locs = [u["loc"] for u in urls]
    assert "https://www.aia-legnano.it/" in locs
    assert "https://www.aia-legnano.it/chi-siamo" in locs
    assert "https://www.aia-legnano.it/eventi" in locs
    assert "https://www.aia-legnano.it/p/pagina-custom" in locs
    assert "https://www.aia-legnano.it/news/vittoria-regionale" in locs
    assert "https://www.aia-legnano.it/arbitri/mario-rossi" in locs
    assert all("/area-associati" not in loc for loc in locs)
    assert all("/amministrazione" not in loc for loc in locs)
