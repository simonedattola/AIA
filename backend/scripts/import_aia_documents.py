"""CLI: importa documenti da https://www.aia-figc.it/download/"""
import asyncio

from app.db import get_db
from app.scrapers.aia_downloads import import_aia_downloads


async def main() -> None:
    db = get_db()
    result = await import_aia_downloads(db)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
