"""Sanitizzazione HTML articoli (TipTap vs import WordPress legacy)."""

from __future__ import annotations

import bleach

from .article_cleanup import repair_body_html
from .sanitize import ALLOWED_ATTRS as TIPTAP_ATTRS
from .sanitize import ALLOWED_TAGS as TIPTAP_TAGS
from .sanitize import sanitize_html

LEGACY_ARTICLE_TAGS = list(
    dict.fromkeys(
        list(TIPTAP_TAGS)
        + [
            "h1",
            "h5",
            "h6",
            "iframe",
            "time",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
        ]
    )
)

LEGACY_ARTICLE_ATTRS = {
    **TIPTAP_ATTRS,
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height", "loading", "class"],
    "iframe": [
        "src",
        "width",
        "height",
        "frameborder",
        "allow",
        "allowfullscreen",
        "style",
        "scrolling",
    ],
    "p": ["style", "class"],
    "span": ["style", "class"],
    "div": ["class", "role", "id", "style"],
    "time": ["datetime", "class"],
    "td": ["colspan", "rowspan", "class"],
    "th": ["colspan", "rowspan", "class"],
}


def sanitize_legacy_article_html(html: str) -> str:
    if not html:
        return ""
    cleaned = bleach.clean(
        html,
        tags=LEGACY_ARTICLE_TAGS,
        attributes=LEGACY_ARTICLE_ATTRS,
        protocols=["http", "https", "mailto"],
        strip=False,
    )
    return repair_body_html(cleaned)


def sanitize_article_html(html: str, *, legacy: bool = False) -> str:
    if legacy:
        return sanitize_legacy_article_html(html)
    return sanitize_html(html)
