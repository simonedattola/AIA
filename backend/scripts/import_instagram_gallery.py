#!/usr/bin/env python3
"""Importa immagini Instagram nel carosello galleria (dal 2021, escluse designazioni).

Per l'archivio completo (~500 post) imposta INSTAGRAM_SESSION_ID nel container:
  1. Accedi a instagram.com nel browser
  2. DevTools → Application → Cookies → sessionid
  3. docker compose up -d con INSTAGRAM_SESSION_ID=... in docker-compose.yml
  4. docker exec aia-backend python scripts/import_instagram_gallery.py --since-year 2021
"""
import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import get_db
from app.instagram_gallery import load_manifest_posts, sync_instagram_gallery


async def main() -> None:
    parser = argparse.ArgumentParser(description="Import Instagram → galleria sito")
    parser.add_argument("--username", default="aia_legnano")
    parser.add_argument("--manifest", help="JSON batch (es. da export browser)")
    parser.add_argument("--limit", type=int, default=0, help="0 = tutti dal since-year")
    parser.add_argument("--since-year", type=int, default=2021)
    args = parser.parse_args()

    db = get_db()
    posts = load_manifest_posts(args.manifest) if args.manifest else None
    result = await sync_instagram_gallery(
        db,
        username=args.username,
        limit=args.limit,
        since_year=args.since_year,
        posts=posts,
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
