"""URL safety unit tests."""
from app.url_safety import is_safe_outbound_url


def test_rejects_private_and_local():
    assert is_safe_outbound_url("http://127.0.0.1/x") is False
    assert is_safe_outbound_url("http://localhost/x") is False
    assert is_safe_outbound_url("http://192.168.1.1/img") is False
    assert is_safe_outbound_url("file:///etc/passwd") is False


def test_rejects_non_http():
    assert is_safe_outbound_url("ftp://example.com/a") is False
    assert is_safe_outbound_url("") is False


def test_allows_public_https():
    # May resolve DNS — use a well-known public host
    assert is_safe_outbound_url("https://example.com/img.jpg") is True


def test_allowlist():
    assert is_safe_outbound_url("https://example.com/a", allowed_hosts={"example.com"}) is True
    assert is_safe_outbound_url("https://evil.com/a", allowed_hosts={"example.com"}) is False
