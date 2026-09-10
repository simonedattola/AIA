"""Tests for AIA HTTP fetch helpers (Cloudflare translate fallback)."""

from app.scrapers.aia_http import (
    translate_proxy_url,
    unwrap_translate_html,
)


def test_unwrap_translate_html_rewrites_host_and_strips_params():
    html = (
        '<a href="https://www-aia--figc-it.translate.goog/designazioni/lombardia/'
        'gir.asp?gare=3-270-SEC&_x_tr_sl=auto&_x_tr_tl=it">x</a>'
    )
    out = unwrap_translate_html(html)
    assert "translate.goog" not in out
    assert "www.aia-figc.it/designazioni/lombardia/gir.asp?gare=3-270-SEC" in out
    assert "_x_tr_" not in out


def test_translate_proxy_url_encodes_target():
    url = "https://www.aia-figc.it/designazioni/lombardia/default.asp?gare=3-270"
    proxied = translate_proxy_url(url)
    assert proxied.startswith("https://translate.google.com/translate?")
    assert "u=https" in proxied
