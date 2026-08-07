"""Sanitize a Page's blocks: walk rich_text bodies and clean HTML."""

import re

import bleach

from .sanitize import sanitize_html

_IG_POST_RE = re.compile(r"instagram\.com/(?:p|reel)/([A-Za-z0-9_-]+)", re.I)


def normalize_instagram_embed_html(html: str) -> str | None:
    """Converte codice embed Instagram (blockquote + script) in iframe sicuro."""
    if not html or not isinstance(html, str):
        return None
    m = re.search(r'data-instgrm-permalink="([^"]+)"', html, re.I)
    haystack = m.group(1) if m else html
    pm = _IG_POST_RE.search(haystack)
    if not pm:
        return None
    code = pm.group(1)
    is_reel = "/reel/" in haystack.lower()
    path = "reel" if is_reel else "p"
    src = f"https://www.instagram.com/{path}/{code}/embed/captioned"
    return (
        f'<iframe src="{src}" width="540" height="700" frameborder="0" '
        f'scrolling="no" allowtransparency="true" loading="lazy" title="Post Instagram"></iframe>'
    )


_EMBED_BLEACH = {
    "tags": ["iframe", "video", "source", "div", "p", "br", "a", "span"],
    "attributes": {
        "iframe": [
            "src",
            "width",
            "height",
            "frameborder",
            "allow",
            "allowfullscreen",
            "title",
            "loading",
            "referrerpolicy",
            "scrolling",
            "allowtransparency",
        ],
        "video": ["src", "controls", "width", "height", "poster"],
        "source": ["src", "type"],
        "a": ["href", "target", "rel"],
        "div": ["class"],
        "span": ["class"],
    },
}


def sanitize_block(b: dict) -> dict:
    if not isinstance(b, dict):
        return b
    t = b.get("type")
    cfg = b.get("config") or {}
    if t == "rich_text" and isinstance(cfg.get("html"), str):
        cfg["html"] = sanitize_html(cfg["html"])
    if t == "text_image" and isinstance(cfg.get("html"), str):
        cfg["html"] = sanitize_html(cfg["html"])
    if t == "faq" and isinstance(cfg.get("items"), list):
        for it in cfg["items"]:
            if isinstance(it.get("answer"), str):
                it["answer"] = sanitize_html(it["answer"])
    if t == "embed" and isinstance(cfg.get("html"), str):
        normalized = normalize_instagram_embed_html(cfg["html"])
        raw = normalized if normalized else cfg["html"]
        cfg["html"] = bleach.clean(
            raw,
            tags=_EMBED_BLEACH["tags"],
            attributes=_EMBED_BLEACH["attributes"],
            protocols=["http", "https"],
            strip=False,
        )
    b["config"] = cfg
    return b


def sanitize_blocks(blocks):
    if not isinstance(blocks, list):
        return []
    return [sanitize_block(b) for b in blocks]
