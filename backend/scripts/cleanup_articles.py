#!/usr/bin/env python3
"""Pulizia articoli legacy: rimuove designazioni, azzera tag WP, ricollega associati."""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.article_cleanup import run_article_cleanup
from app.db import get_db


async def main():
    db = get_db()
    stats = await run_article_cleanup(db)
    print("Pulizia completata:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
