import os

from app.media_urls import resolve_media_url, resolve_html_media_urls


def test_resolve_media_url_localhost_stays_relative(monkeypatch):
    """Local PUBLIC_API_URL must not emit absolute localhost links (breaks tunnels)."""
    monkeypatch.setenv("PUBLIC_API_URL", "http://localhost:8000")
    monkeypatch.delenv("MEDIA_URL_MODE", raising=False)
    assert resolve_media_url("/api/uploads/abc.jpg") == "/api/uploads/abc.jpg"
    assert (
        resolve_media_url("http://localhost:8000/api/uploads/abc.jpg")
        == "/api/uploads/abc.jpg"
    )
    assert resolve_media_url("https://cdn.example/x.jpg") == "https://cdn.example/x.jpg"


def test_resolve_media_url_absolute_when_public(monkeypatch):
    monkeypatch.setenv("PUBLIC_API_URL", "https://api.aia-legnano.it")
    monkeypatch.delenv("MEDIA_URL_MODE", raising=False)
    assert (
        resolve_media_url("/api/uploads/abc.jpg")
        == "https://api.aia-legnano.it/api/uploads/abc.jpg"
    )


def test_resolve_html_media_urls_relative_on_localhost(monkeypatch):
    monkeypatch.setenv("PUBLIC_API_URL", "http://localhost:8000")
    html = '<p><img src="http://localhost:8000/api/uploads/photo.png" alt="x"></p>'
    out = resolve_html_media_urls(html)
    assert 'src="/api/uploads/photo.png"' in out
    assert "localhost" not in out
