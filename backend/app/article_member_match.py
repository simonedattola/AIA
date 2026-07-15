"""Associa articoli ai membri solo se citati per nome e cognome completi."""
from __future__ import annotations

import re
import unicodedata

from bs4 import BeautifulSoup


def _normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", text).strip()


def article_plain_text(title: str, body_html: str, excerpt: str = "") -> str:
    body = BeautifulSoup(body_html or "", "lxml").get_text(" ", strip=True)
    return _normalize_text(f"{title} {excerpt} {body}")


def _word_pattern(phrase: str) -> re.Pattern[str]:
    parts = [re.escape(p) for p in phrase.split() if p]
    inner = r"\s+".join(parts)
    return re.compile(rf"(?<![\wÀ-ÿ]){inner}(?![\wÀ-ÿ])", re.IGNORECASE)


def match_members_by_full_name(
    title: str,
    body_html: str,
    members: list[dict],
    *,
    excerpt: str = "",
) -> list[str]:
    """Restituisce ID membri citati come «Nome Cognome» o «Cognome Nome»."""
    text = article_plain_text(title, body_html, excerpt)
    if not text:
        return []

    found: list[str] = []
    seen: set[str] = set()

    for m in members:
        fn = _normalize_text(m.get("firstName") or "")
        ln = _normalize_text(m.get("lastName") or "")
        mid = m.get("id")
        if not mid or len(fn) < 2 or len(ln) < 2:
            continue
        patterns = (_word_pattern(f"{fn} {ln}"), _word_pattern(f"{ln} {fn}"))
        if any(p.search(text) for p in patterns):
            if mid not in seen:
                seen.add(mid)
                found.append(mid)

    return found
