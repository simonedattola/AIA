#!/usr/bin/env python3
"""Download public WordPress REST content from the old sectional site into JSON.

Does not require WP admin credentials (public endpoints only).
Usage:
  python3 scripts/export_wp_rest.py --base https://www.aia-legnano.it --out backups/wp-export
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


def fetch_json(url: str) -> tuple[object, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "AIA-Legnano-Migration/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        data = json.loads(resp.read().decode("utf-8"))
        return data, headers


def fetch_all(base: str, resource: str, per_page: int = 50) -> list:
    items: list = []
    page = 1
    total_pages = 1
    while page <= total_pages:
        q = urllib.parse.urlencode({"per_page": per_page, "page": page})
        url = f"{base.rstrip('/')}/wp-json/wp/v2/{resource}?{q}"
        print(f"GET {url}")
        data, headers = fetch_json(url)
        if not isinstance(data, list):
            raise SystemExit(f"Unexpected response for {resource}: {type(data)}")
        items.extend(data)
        total_pages = int(headers.get("x-wp-totalpages") or "1")
        page += 1
        time.sleep(0.2)
    return items


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://www.aia-legnano.it")
    ap.add_argument("--out", default="backups/wp-export")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    for resource in ("posts", "pages", "media", "categories", "tags"):
        try:
            items = fetch_all(args.base, resource)
        except Exception as exc:  # noqa: BLE001
            print(f"Skip {resource}: {exc}")
            continue
        path = out / f"{resource}.json"
        path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {path} ({len(items)} items)")

    (out / "source.json").write_text(
        json.dumps({"base": args.base, "note": "Public WP REST export"}, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
