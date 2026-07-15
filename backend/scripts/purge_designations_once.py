"""One-off: purge non-Legnano AIA designations and run short sync."""
import asyncio

from app.db import get_db
from app.designations_sync import sync_from_aia_lombardia


async def main():
    r = await sync_from_aia_lombardia(max_des_pages=2, trigger="cleanup")
    print("sync:", r)
    db = get_db()
    serie = await db.designations.count_documents(
        {"championship": {"$regex": "SERIE A", "$options": "i"}}
    )
    bad = await db.designations.count_documents(
        {
            "source": {"$regex": "^aia-figc"},
            "refereeSection": {"$not": {"$regex": "legnano", "$options": "i"}},
        }
    )
    print("serie_a_remaining:", serie, "aia_without_legnano:", bad)


if __name__ == "__main__":
    asyncio.run(main())
