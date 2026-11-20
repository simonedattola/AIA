"""Authenticated admin media proxy helpers (crop/recrop without browser CORS)."""

from __future__ import annotations

import mimetypes

import httpx
from fastapi import HTTPException
from fastapi.responses import FileResponse, Response

from . import storage as upload_storage
from .media_urls import public_api_base, resolve_media_url


def local_upload_response(path_value: str) -> FileResponse | Response | None:
    name = path_value.rstrip("/").split("/")[-1]
    if not name:
        return None
    data = upload_storage.read_bytes(name)
    if data is None:
        return None
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    local = upload_storage.local_path(name)
    if local is not None:
        return FileResponse(local)
    return Response(content=data, media_type=ctype)


async def proxy_media_url(src: str) -> FileResponse | Response:
    """
    Resolve a relative/absolute media URL to image bytes for admin crop tools.
    Tries local uploads first, then fetches remote HTTP(S) URLs server-side.
    """
    src = (src or "").strip()
    if not src:
        raise HTTPException(404, "Sorgente non disponibile")

    candidates = [src]
    if "/api/uploads/" in src and not src.startswith("/api/uploads/"):
        candidates.append("/api/uploads/" + src.split("/api/uploads/")[-1])

    for candidate in candidates:
        c = (candidate or "").strip()
        if c.startswith("/api/uploads/"):
            found = local_upload_response(c)
            if found:
                return found
        if "/api/uploads/" in c:
            found = local_upload_response(c.split("/api/uploads/")[-1])
            if found:
                return found

    resolved = resolve_media_url(src)
    base = public_api_base()

    if base and resolved.startswith(base):
        rel = resolved[len(base) :]
        if rel.startswith("/api/uploads/"):
            found = local_upload_response(rel)
            if found:
                return found

    if resolved.startswith("http://") or resolved.startswith("https://"):
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                r = await client.get(resolved)
                r.raise_for_status()
            except httpx.HTTPError as exc:
                raise HTTPException(
                    502, f"Impossibile scaricare l'immagine: {exc}"
                ) from exc
            ctype = r.headers.get("content-type", "image/jpeg")
            return Response(content=r.content, media_type=ctype)

    if resolved.startswith("/api/uploads/"):
        found = local_upload_response(resolved)
        if found:
            return found

    raise HTTPException(404, "File non trovato")
