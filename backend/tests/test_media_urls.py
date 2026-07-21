from app.media_urls import resolve_media_url, resolve_html_media_urls


def test_resolve_media_url_with_base(monkeypatch):
    monkeypatch.setenv("PUBLIC_API_URL", "http://localhost:8000")
    assert resolve_media_url("/api/uploads/abc.jpg") == "http://localhost:8000/api/uploads/abc.jpg"
    assert resolve_media_url("https://cdn.example/x.jpg") == "https://cdn.example/x.jpg"


def test_resolve_media_url_rewrites_localhost_absolute(monkeypatch):
    monkeypatch.setenv("PUBLIC_API_URL", "https://api.example.com")
    assert (
        resolve_media_url("http://127.0.0.1:8000/api/uploads/abc.jpg")
        == "https://api.example.com/api/uploads/abc.jpg"
    )
    assert (
        resolve_media_url("http://localhost:8000/api/uploads/abc.jpg")
        == "https://api.example.com/api/uploads/abc.jpg"
    )


def test_resolve_html_media_urls(monkeypatch):
    monkeypatch.setenv("PUBLIC_API_URL", "http://localhost:8000")
    html = '<p><img src="/api/uploads/photo.png" alt="x"></p>'
    out = resolve_html_media_urls(html)
    assert "http://localhost:8000/api/uploads/photo.png" in out
