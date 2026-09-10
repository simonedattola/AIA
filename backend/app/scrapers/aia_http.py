"""HTTP helpers for AIA FIGC pages (Cloudflare often blocks datacenter IPs).

When a direct request gets 403 / challenge HTML, fall back to Google Translate
as a fetch proxy — it returns usable designazioni HTML from Railway Free.
"""

from __future__ import annotations

import logging
import os
import re
import urllib.parse
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

_TRANSLATE_HOST_RE = re.compile(
    r"https?://www-aia-+figc-it\.translate\.goog",
    re.I,
)
_X_TR_PARAM_RE = re.compile(r"([?&])_x_tr_[^=&]+=[^&\"'\s>]*")


def fetch_mode() -> str:
    raw = (os.environ.get("AIA_FETCH_MODE") or "auto").strip().lower()
    if raw in ("direct", "translate", "auto"):
        return raw
    return "auto"


def _is_challenge(html: str, status_code: int) -> bool:
    if status_code in (401, 403, 503):
        return True
    low = (html or "")[:4000].lower()
    return (
        "just a moment" in low
        or "cf-browser-verification" in low
        or "cdn-cgi/challenge" in low
        or ("cloudflare" in low and "attention required" in low)
    )


def unwrap_translate_html(html: str) -> str:
    """Rewrite translate.goog links back to www.aia-figc.it and drop _x_tr_ params."""
    text = _TRANSLATE_HOST_RE.sub("https://www.aia-figc.it", html or "")
    text = _X_TR_PARAM_RE.sub(r"\1", text)
    text = re.sub(r"\?&", "?", text)
    text = re.sub(r"\?([\"'\s>])", r"\1", text)
    text = re.sub(r"&&+", "&", text)
    return text


def translate_proxy_url(url: str) -> str:
    return (
        "https://translate.google.com/translate?sl=auto&tl=it&u="
        + urllib.parse.quote(url, safe="")
    )


def fetch_aia_html(
    url: str,
    *,
    client: Optional[httpx.Client] = None,
    timeout: float = 45.0,
    headers: Optional[dict] = None,
) -> str:
    """
    Fetch an AIA FIGC URL as HTML.

    ``AIA_FETCH_MODE``:
      - ``direct``: only direct httpx
      - ``translate``: always via Google Translate proxy
      - ``auto`` (default): direct, then translate on Cloudflare challenge/403
    """
    hdrs = dict(DEFAULT_HEADERS)
    if headers:
        hdrs.update(headers)
    mode = fetch_mode()
    own = client is None
    if own:
        client = httpx.Client(headers=hdrs, timeout=timeout, follow_redirects=True)

    try:
        if mode != "translate":
            try:
                r = client.get(url, headers=hdrs, follow_redirects=True)
                body = r.text or ""
                if r.status_code == 200 and not _is_challenge(body, r.status_code):
                    return body
                logger.warning(
                    "AIA direct fetch blocked (%s %s); trying translate proxy",
                    r.status_code,
                    url,
                )
            except Exception as exc:
                if mode == "direct":
                    raise
                logger.warning(
                    "AIA direct fetch error (%s): %s; trying translate", url, exc
                )

        if mode == "direct":
            raise RuntimeError(f"AIA direct fetch failed for {url}")

        proxy = translate_proxy_url(url)
        r = client.get(proxy, headers=hdrs, follow_redirects=True)
        r.raise_for_status()
        body = unwrap_translate_html(r.text or "")
        if _is_challenge(body, r.status_code) or (
            "translate.google" in body[:500].lower()
            and "gare=" not in body.lower()
            and "designazioni" not in body.lower()
        ):
            # Still usable if designazioni markers exist after unwrap
            if (
                "gir.asp" not in body.lower()
                and "des.asp" not in body.lower()
                and "arbitro" not in body.lower()
            ):
                raise RuntimeError(
                    f"AIA translate proxy returned challenge/empty for {url}"
                )
        return body
    finally:
        if own:
            client.close()
