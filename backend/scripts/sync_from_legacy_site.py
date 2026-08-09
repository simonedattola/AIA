#!/usr/bin/env python3
"""Sync images and download files from the legacy site https://www.aia-legnano.it

This script is intended to be executed in CI (GitHub Actions) from the repository root.
It downloads media from the WordPress REST API, images from the posts and the /galleria/
page, and the files linked on /download/. Processed images and files are written under
<output_dir>/images/... and <output_dir>/downloads/.

Usage (in the action we run):
  python3 backend/scripts/sync_from_legacy_site.py --output-dir=static

Notes:
- The script is conservative: it sanitizes filenames and avoids re-downloading files
  already present with the same size.
- Images are cropped to 16:9 (landscape) or 9:16 (portrait) depending on orientation,
  resized (long side <= 1920px) and saved as JPEG with reasonable quality to keep
  sizes small.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from PIL import Image

WP_BASE = "https://www.aia-legnano.it"
WP_API = f"{WP_BASE.rstrip('/')}/wp-json/wp/v2"
GALLERY_PAGE = f"{WP_BASE.rstrip('/')}/galleria/"
DOWNLOAD_PAGE = f"{WP_BASE.rstrip('/')}/download/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AIA-Legnano-CMS/1.0; +https://www.aia-legnano.it)",
}

IMAGE_MAX_LONG_SIDE = 1920
JPEG_QUALITY = 80

VALID_DOWNLOAD_EXT = (".pdf", ".doc", ".docx", ".zip", ".pptx", ".mp3", ".xlsx")

def sanitize_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[\\/:\*\?\"<>|]+", "-", name)
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"[^\w.\-]+", "", name)
    return name[:200]

def ensure_dirs(base: Path):
    (base / "images" / "articles").mkdir(parents=True, exist_ok=True)
    (base / "images" / "carousel").mkdir(parents=True, exist_ok=True)
    (base / "downloads").mkdir(parents=True, exist_ok=True)

def fetch_wp_media(client: httpx.Client) -> list[dict]:
    items = []
    page = 1
    per_page = 100
    while True:
        url = f"{WP_API}/media"
        params = {"per_page": per_page, "page": page}
        r = client.get(url, params=params, timeout=30.0)
        if r.status_code != 200:
            break
        data = r.json()
        if not isinstance(data, list) or not data:
            break
        items.extend(data)
        if len(data) < per_page:
            break
        page += 1
    return items

def download_file(client: httpx.Client, url: str, dest: Path) -> bool:
    url = url or ""
    if not url:
        return False
    try:
        resp = client.get(url, timeout=60.0)
        resp.raise_for_status()
    except Exception:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = resp.content
    if dest.exists() and dest.stat().st_size == len(content):
        return True
    dest.write_bytes(content)
    return True

def crop_to_aspect(img: Image.Image, target_aspect: float) -> Image.Image:
    w, h = img.size
    current = w / h
    if abs(current - target_aspect) < 1e-3:
        return img
    if current > target_aspect:
        # too wide -> crop width
        new_w = int(target_aspect * h)
        left = (w - new_w) // 2
        return img.crop((left, 0, left + new_w, h))
    else:
        # too tall -> crop height
        new_h = int(w / target_aspect)
        top = (h - new_h) // 2
        return img.crop((0, top, w, top + new_h))

def process_image(in_path: Path, out_path: Path):
    try:
        with Image.open(in_path) as im:
            im = im.convert("RGB")
            w, h = im.size
            if w >= h:
                # landscape -> 16:9
                target_aspect = 16 / 9
            else:
                target_aspect = 9 / 16
            im = crop_to_aspect(im, target_aspect)
            # resize: long side <= IMAGE_MAX_LONG_SIDE
            w, h = im.size
            if w >= h:
                if w > IMAGE_MAX_LONG_SIDE:
                    new_w = IMAGE_MAX_LONG_SIDE
                    new_h = int(new_w * h / w)
                else:
                    new_w, new_h = w, h
            else:
                if h > IMAGE_MAX_LONG_SIDE:
                    new_h = IMAGE_MAX_LONG_SIDE
                    new_w = int(new_h * w / h)
                else:
                    new_w, new_h = w, h
            im = im.resize((new_w, new_h), Image.LANCZOS)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path_temp = out_path.with_suffix(".tmpjpg")
            im.save(out_path_temp, format="JPEG", quality=JPEG_QUALITY, optimize=True)
            out_path_temp.replace(out_path)
            return True
    except Exception:
        return False

def collect_post_image_urls(client: httpx.Client) -> set[str]:
    urls = set()
    page = 1
    per_page = 100
    while True:
        url = f"{WP_API}/posts"
        params = {"per_page": per_page, "page": page}
        r = client.get(url, params=params, timeout=30.0)
        if r.status_code != 200:
            break
        data = r.json()
        if not isinstance(data, list) or not data:
            break
        for p in data:
            content = p.get("content", {}).get("rendered", "")
            soup = BeautifulSoup(content, "html.parser")
            for img in soup.select("img[src]"):
                urls.add(urljoin(WP_BASE, img.get("src")))
        if len(data) < per_page:
            break
        page += 1
    return urls

def fetch_gallery_images(client: httpx.Client) -> set[str]:
    urls = set()
    try:
        r = client.get(GALLERY_PAGE, timeout=30.0)
        r.raise_for_status()
    except Exception:
        return urls
    soup = BeautifulSoup(r.text, "html.parser")
    for img in soup.select("img[src]"):
        src = img.get("src") or ""
        if src:
            urls.add(urljoin(GALLERY_PAGE, src))
    return urls

def fetch_download_links(client: httpx.Client) -> list[tuple[str, str]]:
    out = []
    try:
        r = client.get(DOWNLOAD_PAGE, timeout=30.0)
        r.raise_for_status()
    except Exception:
        return out
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.select("a[href]"):
        href = a.get("href") or ""
        full = urljoin(DOWNLOAD_PAGE, href)
        path = urlparse(full).path.lower()
        if any(path.endswith(ext) for ext in VALID_DOWNLOAD_EXT) or "/documents/" in path:
            title = (a.get_text(" ", strip=True) or Path(path).name)
            out.append((title, full))
    for a in soup.select("a[href]"):
        href = a.get("href") or ""
        if "aia-figc.it" in href:
            full = href
            title = a.get_text(" ", strip=True) or Path(urlparse(href).path).name
            out.append((title, full))
    seen = set()
    res = []
    for t, u in out:
        if u in seen:
            continue
        seen.add(u)
        res.append((t, u))
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="static", help="Output base dir (relative to repo root)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base = Path(args.output_dir)
    ensure_dirs(base)

    client = httpx.Client(headers=HEADERS, follow_redirects=True, timeout=60.0)

    report = {
        "images_downloaded": [],
        "downloads_retrieved": [],
        "errors": [],
    }

    try:
        # 1) WP media
        try:
            media = fetch_wp_media(client)
        except Exception as exc:
            media = []
            report["errors"].append(f"fetch_wp_media: {exc}")

        media_urls = set()
        for m in media:
            src = m.get("source_url") or m.get("guid", {}).get("rendered") if isinstance(m.get("guid"), dict) else None
            if not src:
                continue
            media_urls.add(src)

        # 2) post images
        try:
            post_imgs = collect_post_image_urls(client)
            media_urls.update(post_imgs)
        except Exception as exc:
            report["errors"].append(f"collect_post_image_urls: {exc}")

        # 3) gallery images
        try:
            gal = fetch_gallery_images(client)
            media_urls.update(gal)
        except Exception as exc:
            report["errors"].append(f"fetch_gallery_images: {exc}")

        # Download and process images
        for url in sorted(media_urls):
            parsed = urlparse(url)
            name = sanitize_filename(Path(parsed.path).name or hashlib.md5(url.encode()).hexdigest())
            if not Path(name).suffix:
                name = name + ".jpg"
            dest_dir = base / "images" / ("carousel" if "galleria" in parsed.path.lower() or "gallery" in parsed.path.lower() else "articles")
            dest_path_raw = dest_dir / name
            dest_path_proc = dest_path_raw.with_suffix(".jpg")
            if dest_path_proc.exists():
                report["images_downloaded"].append({"url": url, "path": str(dest_path_proc), "skipped": True})
                continue
            tmp = dest_path_raw.with_suffix(".tmp")
            ok = download_file(client, url, tmp)
            if not ok:
                report["errors"].append(f"failed download image {url}")
                continue
            try:
                processed = process_image(tmp, dest_path_proc)
                if processed:
                    tmp.unlink(missing_ok=True)
                    report["images_downloaded"].append({"url": url, "path": str(dest_path_proc)})
                else:
                    report["errors"].append(f"processing failed {url}")
            except Exception as exc:
                report["errors"].append(f"processing exception {url}: {exc}")

        # Fetch downloads
        try:
            downloads = fetch_download_links(client)
        except Exception as exc:
            downloads = []
            report["errors"].append(f"fetch_download_links: {exc}")

        for title, url in downloads:
            parsed = urlparse(url)
            rawname = Path(parsed.path).name or hashlib.md5(url.encode()).hexdigest()
            name = sanitize_filename(rawname)
            if not Path(name).suffix:
                name += ""
            dest = base / "downloads" / name
            if dest.exists():
                report["downloads_retrieved"].append({"url": url, "path": str(dest), "skipped": True})
                continue
            ok = download_file(client, url, dest)
            if ok:
                report["downloads_retrieved"].append({"url": url, "path": str(dest)})
            else:
                report["errors"].append(f"failed download file {url}")

    finally:
        client.close()

    rpt_path = Path("sync_aia_report.json")
    rpt_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
