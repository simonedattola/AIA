"""Download foto galleria area associati."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import portal as portal_routes


def _app_with_member(member_id: str = "m1") -> TestClient:
    app = FastAPI()
    app.include_router(portal_routes.router)

    async def _member():
        return {"memberId": member_id, "role": "member"}

    app.dependency_overrides[portal_routes.require_member] = _member
    return TestClient(app)


@pytest.mark.asyncio
async def test_portal_media_download_forces_attachment(monkeypatch):
    jpeg = b"\xff\xd8\xff\xd9fakejpeg"
    doc = {
        "id": "img-1",
        "status": "approved",
        "memberIds": ["m1"],
        "url": "/api/uploads/photo.jpg",
        "path": "/api/uploads/photo.jpg",
        "caption": "Raduno primavera",
        "photoDate": "2026-05-10",
    }

    fake_db = MagicMock()
    fake_db.gallery_images.find_one = AsyncMock(return_value=doc)

    monkeypatch.setattr(portal_routes, "get_db", lambda: fake_db)

    with patch("app.routes.portal.upload_storage.read_bytes", return_value=jpeg):
        client = _app_with_member("m1")
        r = client.get("/api/portal/media/img-1/download")

    assert r.status_code == 200
    assert r.content == jpeg
    cd = r.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "aia-legnano-raduno-primavera" in cd.lower()
    assert "filename=" in cd


@pytest.mark.asyncio
async def test_portal_media_download_forbidden_if_not_tagged(monkeypatch):
    fake_db = MagicMock()
    fake_db.gallery_images.find_one = AsyncMock(return_value=None)
    monkeypatch.setattr(portal_routes, "get_db", lambda: fake_db)

    client = _app_with_member("m1")
    r = client.get("/api/portal/media/img-x/download")
    assert r.status_code == 404
