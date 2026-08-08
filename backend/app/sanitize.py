"""HTML sanitizer for article bodyHtml coming from TipTap."""

import bleach

ALLOWED_TAGS = [
    "p",
    "br",
    "hr",
    "h2",
    "h3",
    "h4",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "code",
    "a",
    "ul",
    "ol",
    "li",
    "blockquote",
    "pre",
    "img",
    "figure",
    "figcaption",
    "span",
    "div",
]

ALLOWED_ATTRS = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height", "loading"],
    "span": ["class"],
    "div": ["class"],
    "p": ["class"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html(html: str) -> str:
    if not html:
        return ""
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    # Force external links to be safe
    cleaned = bleach.linkify(
        cleaned,
        callbacks=[
            lambda attrs, new=False: {
                **attrs,
                (None, "target"): "_blank",
                (None, "rel"): "noopener noreferrer",
            }
        ],
        skip_tags=["pre", "code"],
    )
    return cleaned
