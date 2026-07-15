"""Pulizia articoli importati dal sito legacy."""
from __future__ import annotations

import html as html_lib
import logging
import re
from typing import Any

from bs4 import BeautifulSoup

from .article_body import normalize_article_body_html
from .article_member_match import article_plain_text, match_members_by_full_name
from .models import _now

logger = logging.getLogger(__name__)

DESIGNATIONS_TITLE = re.compile(
    r"^designazioni(\s|$|[-:])",
    re.IGNORECASE,
)

DESIGNATIONS_BODY = re.compile(
    r"\bGARA\s*:\s*",
    re.IGNORECASE,
)


def is_weekly_designations_article(doc: dict) -> bool:
    title = (doc.get("title") or "").strip()
    slug = (doc.get("slug") or "").strip()
    if slug.startswith("designazioni"):
        return True
    if DESIGNATIONS_TITLE.search(title):
        return True
    text = article_plain_text(title, doc.get("bodyHtml") or "", doc.get("excerpt") or "")
    if DESIGNATIONS_BODY.search(text) and text.lower().count("girone") >= 2:
        return True
    if text.count("GARA :") + text.count("GARA:") >= 4:
        return True
    return False


def has_broken_form_content(body_html: str) -> bool:
    low = (body_html or "").lower()
    return "wpcf7" in low or "your-surname" in low or "your-name" in low


def repair_body_html(body_html: str) -> str:
    if not body_html:
        return ""
    fixed = html_lib.unescape(body_html)
    soup = BeautifulSoup(fixed, "lxml")
    for tag in soup.select("div.wpcf7, form.wpcf7-form, script"):
        tag.decompose()
    body = soup.body
    if body:
        inner = "".join(str(c) for c in body.children)
    else:
        inner = str(soup)
    return normalize_article_body_html(inner.strip())


async def run_article_cleanup(db) -> dict[str, Any]:
    members = await db.members.find(
        {}, {"_id": 0, "id": 1, "firstName": 1, "lastName": 1}
    ).to_list(500)

    stats: dict[str, Any] = {
        "deleted_designations": 0,
        "deleted_broken": 0,
        "updated": 0,
        "tags_cleared": 0,
        "members_relinked": 0,
    }

    to_delete: list[str] = []
    async for doc in db.articles.find({}, {"_id": 0, "id": 1, "slug": 1, "title": 1, "bodyHtml": 1, "excerpt": 1}):
        if is_weekly_designations_article(doc):
            to_delete.append(doc["id"])
            stats["deleted_designations"] += 1
        elif has_broken_form_content(doc.get("bodyHtml") or ""):
            to_delete.append(doc["id"])
            stats["deleted_broken"] += 1

    if to_delete:
        await db.articles.delete_many({"id": {"$in": to_delete}})

    async for doc in db.articles.find({}, {"_id": 0}):
        article_id = doc["id"]
        title = html_lib.unescape(doc.get("title") or "")
        body = repair_body_html(doc.get("bodyHtml") or "")
        excerpt = html_lib.unescape(_strip_excerpt(doc.get("excerpt") or "", body))

        related = match_members_by_full_name(title, body, members, excerpt=excerpt)
        patch = {
            "title": title,
            "bodyHtml": body,
            "excerpt": excerpt,
            "tags": [],
            "relatedMemberIds": related,
            "updatedAt": _now(),
        }

        changed = (
            doc.get("title") != title
            or doc.get("bodyHtml") != body
            or doc.get("excerpt") != excerpt
            or (doc.get("tags") or []) != []
            or (doc.get("relatedMemberIds") or []) != related
        )
        if changed:
            await db.articles.update_one({"id": article_id}, {"$set": patch})
            stats["updated"] += 1
            if doc.get("tags"):
                stats["tags_cleared"] += 1
            if related:
                stats["members_relinked"] += 1

    stats["remaining"] = await db.articles.count_documents({})
    return stats


def _strip_excerpt(excerpt: str, body_html: str) -> str:
    ex = (excerpt or "").strip()
    if ex and not ex.endswith("[…]") and "hellip" not in ex:
        return ex
    plain = article_plain_text("", body_html)
    return (plain[:280] + "…") if len(plain) > 280 else plain
