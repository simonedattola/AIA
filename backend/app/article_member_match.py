"""Associa articoli ai membri solo se citati per nome e cognome completi."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from bs4 import BeautifulSoup, NavigableString


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


def _member_name_phrases(member: dict) -> list[str]:
    fn = _normalize_text(member.get("firstName") or "")
    ln = _normalize_text(member.get("lastName") or "")
    if len(fn) < 2 or len(ln) < 2:
        return []
    return [f"{fn} {ln}", f"{ln} {fn}"]


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
        mid = m.get("id")
        phrases = _member_name_phrases(m)
        if not mid or not phrases:
            continue
        patterns = tuple(_word_pattern(p) for p in phrases)
        if any(p.search(text) for p in patterns):
            if mid not in seen:
                seen.add(mid)
                found.append(mid)

    return found


def merge_related_member_ids(
    existing: list[str] | None, matched: list[str] | None
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for mid in list(existing or []) + list(matched or []):
        if not mid or mid in seen:
            continue
        seen.add(mid)
        out.append(mid)
    return out


def apply_auto_related_members(
    article: dict[str, Any],
    members: list[dict],
) -> list[str]:
    """relatedMemberIds manuali ∪ match automatico da nome+cognome nel testo."""
    matched = match_members_by_full_name(
        article.get("title") or "",
        article.get("bodyHtml") or "",
        members,
        excerpt=article.get("excerpt") or "",
    )
    return merge_related_member_ids(article.get("relatedMemberIds"), matched)


def _inside_anchor(node) -> bool:
    parent = getattr(node, "parent", None)
    while parent is not None:
        name = getattr(parent, "name", None)
        if name == "a":
            return True
        parent = getattr(parent, "parent", None)
    return False


def linkify_member_names_in_html(
    html: str,
    members: list[dict],
    *,
    href_prefix: str = "/arbitri/",
) -> str:
    """Avvolge «Nome Cognome» / «Cognome Nome» in link al profilo pubblico."""
    if not (html or "").strip() or not members:
        return html or ""

    # Frasi più lunghe prima (evita match parziali su omonimi)
    candidates: list[tuple[re.Pattern[str], str, str]] = []
    for m in members:
        slug = (m.get("slug") or "").strip()
        mid = m.get("id")
        if not slug or not mid:
            continue
        href = f"{href_prefix.rstrip('/')}/{slug}"
        for phrase in _member_name_phrases(m):
            candidates.append((_word_pattern(phrase), href, phrase))
    candidates.sort(key=lambda c: len(c[2]), reverse=True)
    if not candidates:
        return html

    soup = BeautifulSoup(html, "lxml")
    # Itera su una copia: la modifica invalida il tree durante il walk
    text_nodes = [
        node
        for node in soup.find_all(string=True)
        if isinstance(node, NavigableString)
        and node.parent
        and node.parent.name not in ("script", "style", "code", "pre")
        and not _inside_anchor(node)
        and str(node).strip()
    ]

    for node in text_nodes:
        original = str(node)
        if not original.strip():
            continue
        pieces: list[Any] = []
        cursor = 0
        matches: list[tuple[int, int, str]] = []
        for pattern, href, _phrase in candidates:
            for m in pattern.finditer(original):
                start, end = m.start(), m.end()
                # Skip overlapping
                if any(not (end <= s or start >= e) for s, e, _ in matches):
                    continue
                matches.append((start, end, href))
        if not matches:
            continue
        matches.sort(key=lambda t: t[0])
        for start, end, href in matches:
            if start > cursor:
                pieces.append(original[cursor:start])
            a = soup.new_tag(
                "a",
                href=href,
                **{
                    "class": "aia-member-tag",
                    "data-member-link": "1",
                },
            )
            a.string = original[start:end]
            pieces.append(a)
            cursor = end
        if cursor < len(original):
            pieces.append(original[cursor:])
        node.replace_with(*pieces)

    body = soup.body
    if body is not None:
        return "".join(str(c) for c in body.contents)
    return str(soup)
