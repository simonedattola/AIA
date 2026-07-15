#!/usr/bin/env python3
import asyncio
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bs4 import BeautifulSoup
from app.db import get_db


def plain(html: str) -> str:
    return BeautifulSoup(html or "", "lxml").get_text(" ", strip=True)


async def main():
    db = get_db()
    rows = []
    async for a in db.articles.find({}, {"_id": 0}).sort("publishedAt", -1):
        body = a.get("bodyHtml") or ""
        title = a.get("title") or ""
        text = plain(body)
        rows.append(
            {
                "slug": a.get("slug"),
                "title": title,
                "len": len(text),
                "tags": a.get("tags") or [],
                "rel": a.get("relatedMemberIds") or [],
                "wp": a.get("legacyWpId"),
            }
        )

    des = [r for r in rows if re.search(r"designazioni", r["title"], re.I)]
    print("designazioni titles", len(des))
    for r in des[:15]:
        print(r["slug"], r["len"], r["tags"][:3])

    short = [r for r in rows if r["len"] < 200]
    print("\nvery short", len(short))
    for r in short:
        print(r["slug"], r["title"][:55], r["len"])

    with_tags = [r for r in rows if r["tags"]]
    print("\nwith tags", len(with_tags))


if __name__ == "__main__":
    asyncio.run(main())
