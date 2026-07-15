#!/usr/bin/env python3
"""Importa batch Instagram da JSON (posts con imageDataUrl) verso MongoDB."""
import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import get_db
from app.instagram_gallery import import_instagram_batch, load_manifest_posts


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", help="JSON batch con campo posts")
    args = parser.parse_args()

    posts = load_manifest_posts(args.manifest)
    if isinstance(posts, dict) and "posts" in posts:
        posts = posts["posts"]
    db = get_db()
    result = await import_instagram_batch(db, posts)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
