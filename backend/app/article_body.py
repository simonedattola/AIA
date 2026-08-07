"""Normalizzazione HTML corpo articolo (gallerie legacy WordPress / BWG)."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

_BWG_STYLE_ID = re.compile(r"^bwg-style", re.I)
_BWG_CONTAINER_ID = re.compile(r"^bwg_container1_", re.I)
_BWG_ORPHAN_ID = re.compile(
    r"^(spider_popup_overlay|bwg_spider_popup_loading|ajax_loading|loading_div|bwg_random_seed|page_number)_",
    re.I,
)


def _img_payload(img: Tag) -> dict[str, str] | None:
    src = (img.get("src") or "").strip()
    if not src:
        return None
    return {"src": src, "alt": (img.get("alt") or "").strip()}


def _make_carousel_tag(soup: BeautifulSoup, images: list[dict[str, str]]) -> Tag:
    div = soup.new_tag("div", attrs={"class": "aia-article-carousel"})
    for item in images:
        img = soup.new_tag("img")
        img["src"] = item["src"]
        if item.get("alt"):
            img["alt"] = item["alt"]
        img["loading"] = "lazy"
        div.append(img)
    return div


def _strip_bwg_galleries(soup: BeautifulSoup) -> None:
    for style in soup.find_all("style", id=_BWG_STYLE_ID):
        style.decompose()

    containers = soup.find_all("div", id=_BWG_CONTAINER_ID)
    for container in containers:
        images: list[dict[str, str]] = []
        seen: set[str] = set()
        for img in container.find_all("img"):
            payload = _img_payload(img)
            if not payload or payload["src"] in seen:
                continue
            seen.add(payload["src"])
            images.append(payload)

        if images:
            container.replace_with(_make_carousel_tag(soup, images))
        else:
            container.decompose()

    for tag in soup.find_all(["div", "input", "form"]):
        tag_id = tag.get("id") or ""
        if _BWG_ORPHAN_ID.match(tag_id):
            tag.decompose()
            continue
        classes = " ".join(tag.get("class") or [])
        if "spider_popup_overlay" in classes or "bwg_spider_popup_loading" in classes:
            tag.decompose()
            continue
        if tag.name == "form" and "bwg" in classes:
            tag.decompose()


def normalize_article_body_html(body_html: str) -> str:
    """Ripulisce markup legacy e converte gallerie BWG in caroselli semantici."""
    if not body_html:
        return ""
    soup = BeautifulSoup(body_html, "lxml")
    _strip_bwg_galleries(soup)
    body = soup.body
    if body:
        return "".join(str(c) for c in body.children).strip()
    return str(soup).strip()
