#!/usr/bin/env python3
"""Importa articoli da https://www.aia-legnano.it/ (WordPress REST API).

Uso:
  python scripts/import_legacy_articles.py
  python scripts/import_legacy_articles.py --dry-run
  python scripts/import_legacy_articles.py --no-images
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

# backend/ come root per import app.*
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.db import get_db  # noqa: E402
from app.legacy_article_import import run_legacy_article_import  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser(description="Import articoli dal sito legacy AIA Legnano")
    parser.add_argument("--dry-run", action="store_true", help="Simula senza scrivere su DB")
    parser.add_argument("--no-images", action="store_true", help="Non scaricare immagini in locale")
    args = parser.parse_args()

    db = get_db()
    stats = await run_legacy_article_import(
        db,
        dry_run=args.dry_run,
        download_images=not args.no_images,
    )
    print("Import completato:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
