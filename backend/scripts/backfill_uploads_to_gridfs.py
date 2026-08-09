#!/usr/bin/env python3
"""Carica su MongoDB GridFS i file `/api/uploads/*` referenziati dal DB.

Utile quando Atlas ha i metadati (articoli/documenti) ma Railway non trova i
byte (404). Sorgenti in ordine:
  1. file già presenti in backend/uploads/
  2. (opzionale) --from-legacy: riscarica da https://www.aia-legnano.it

Uso:
  cd backend && python scripts/backfill_uploads_to_gridfs.py
  python scripts/backfill_uploads_to_gridfs.py --from-legacy
"""
from __future__ import annotations

import argparse
import asyncio
import mimetypes
import os
import re
import sys
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gridfs import GridFS  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from pymongo import MongoClient  # noqa: E402

from app.paths import UPLOAD_DIR  # noqa: E402


def _name_from_upload_url(url: str) -> str | None:
    if not url or "/api/uploads/" not in url:
        return None
    return url.split("/api/uploads/", 1)[-1].split("?", 1)[0].strip() or None


async def collect_refs(db) -> set[str]:
    refs: set[str] = set()
    async for a in db.articles.find({}, {"coverUrl": 1, "bodyHtml": 1}):
        n = _name_from_upload_url(a.get("coverUrl") or "")
        if n:
            refs.add(n)
        for m in re.findall(r"/api/uploads/([^\"'?\\s]+)", a.get("bodyHtml") or ""):
            refs.add(m)
    async for d in db.documents.find({}, {"fileUrl": 1}):
        n = _name_from_upload_url(d.get("fileUrl") or "")
        if n:
            refs.add(n)
    async for g in db.gallery_images.find({}, {"url": 1, "path": 1, "sourceUrl": 1}):
        for key in ("url", "path"):
            n = _name_from_upload_url(g.get(key) or "")
            if n:
                refs.add(n)
    return refs


def put_bytes(fs: GridFS, name: str, data: bytes) -> None:
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    for doc in fs.find({"filename": name}):
        fs.delete(doc._id)
    fs.put(data, filename=name, contentType=ctype)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill uploads into MongoDB GridFS")
    parser.add_argument(
        "--from-legacy",
        action="store_true",
        help="Se manca in locale, tenta di scaricare da aia-legnano.it (solo path /documents/ e wp-content)",
    )
    args = parser.parse_args()

    mongo = os.environ["MONGO_URL"]
    db_name = os.environ.get("DB_NAME") or "aia_legnano"
    adb = AsyncIOMotorClient(mongo)[db_name]
    sync = MongoClient(mongo)
    fs = GridFS(sync[db_name], collection="uploads")

    refs = await collect_refs(adb)
    already = local = missing = 0
    uploaded = 0

    import httpx

    async with httpx.AsyncClient(
        headers={"User-Agent": "AIA-Legnano-CMS/1.0"},
        follow_redirects=True,
        timeout=60.0,
    ) as http:
        for name in sorted(refs):
            if fs.exists({"filename": name}):
                already += 1
                continue
            path = UPLOAD_DIR / name
            data = None
            if path.is_file() and path.stat().st_size > 0:
                data = path.read_bytes()
                local += 1
            elif args.from_legacy:
                # best-effort: legnano documents keep original basename sometimes
                candidates = [
                    f"https://www.aia-legnano.it/documents/{name}",
                    f"https://www.aia-legnano.it/wp-content/uploads/{name}",
                ]
                for url in candidates:
                    try:
                        r = await http.get(url)
                        if r.status_code == 200 and len(r.content) > 200 and "text/html" not in (
                            r.headers.get("content-type") or ""
                        ):
                            data = r.content
                            path.write_bytes(data)
                            break
                    except Exception:
                        pass
            if not data:
                missing += 1
                continue
            put_bytes(fs, name, data)
            uploaded += 1
            if uploaded % 50 == 0:
                print(f"uploaded {uploaded}…")

    print(
        f"refs={len(refs)} already={already} uploaded={uploaded} "
        f"from_local_or_legacy={local} still_missing={missing}"
    )
    sync.close()


if __name__ == "__main__":
    asyncio.run(main())
