from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.instagram_widget import (
    _merge_posts,
    build_instagram_widget_payload,
    fetch_instagram_widget_sync,
    get_instagram_widget_data,
    save_widget_cache,
    load_widget_cache,
)


def test_merge_posts_prefers_live_then_gallery():
    live = [
        {"shortcode": "A", "permalink": "https://instagram.com/p/A/", "imageUrl": "a"}
    ]
    gallery = [
        {"shortcode": "A", "permalink": "https://instagram.com/p/A/", "imageUrl": "a2"},
        {"shortcode": "B", "permalink": "https://instagram.com/p/B/", "imageUrl": "b"},
    ]
    merged = _merge_posts(live, gallery, limit=4)
    assert len(merged) == 2
    assert merged[0]["imageUrl"] == "a"
    assert merged[1]["shortcode"] == "B"


def test_fetch_instagram_widget_sync_structure():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {
        "user": {
            "username": "aia_legnano",
            "full_name": "AIA Legnano",
            "profile_pic_url": "https://cdn.example/pic.jpg",
            "is_verified": False,
        },
        "items": [
            {
                "code": "AbC123",
                "media_type": 1,
                "product_type": "feed",
                "caption": {"text": "Ciao"},
                "image_versions2": {
                    "candidates": [{"url": "https://cdn.example/post.jpg"}]
                },
            }
        ],
    }
    with patch("app.instagram_widget.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value.get.return_value = mock_response
        data = fetch_instagram_widget_sync("aia_legnano", limit=4)
    assert data["profile"]["username"] == "aia_legnano"
    assert len(data["posts"]) == 1
    assert data["posts"][0]["permalink"].endswith("/p/AbC123/")
    assert "/api/public/instagram/media/AbC123" in data["posts"][0]["imageUrl"]


def test_fetch_instagram_widget_retries_after_401():
    fail = MagicMock()
    fail.status_code = 401
    fail.headers = {"content-type": "application/json"}
    fail.json.return_value = {"message": "fail"}

    ok = MagicMock()
    ok.status_code = 200
    ok.headers = {"content-type": "application/json"}
    ok.json.return_value = {
        "user": {"username": "aia_legnano", "full_name": "AIA", "profile_pic_url": ""},
        "items": [
            {
                "code": "Retry1",
                "media_type": 1,
                "image_versions2": {
                    "candidates": [{"url": "https://cdn.example/r.jpg"}]
                },
            }
        ],
    }

    with patch("app.instagram_widget.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.get.side_effect = [fail, ok]
        data = fetch_instagram_widget_sync("aia_legnano", limit=4)
    assert data["posts"][0]["shortcode"] == "Retry1"


@pytest.mark.asyncio
async def test_get_instagram_widget_data_with_stats():
    with patch(
        "app.instagram_widget.fetch_instagram_widget_sync",
        return_value={
            "profile": {"username": "aia_legnano"},
            "posts": [{"shortcode": "X", "imageUrl": "u", "permalink": "p"}],
        },
    ):
        data = await get_instagram_widget_data(
            "aia_legnano",
            limit=4,
            stats={"posts": 100, "followers": 1200, "following": 50},
        )
    assert data["stats"]["posts"] == 100
    assert data["stats"]["followers"] == 1200
    assert data["stats"]["following"] == 50


@pytest.mark.asyncio
async def test_build_widget_uses_gallery_when_live_empty():
    class FakeCursor:
        def sort(self, *_a, **_k):
            return self

        async def to_list(self, _limit):
            return [
                {
                    "id": "g1",
                    "url": "/uploads/ig1.jpg",
                    "sourceUrl": "https://www.instagram.com/p/ZZZ/",
                    "caption": "Evento",
                }
            ]

    db = MagicMock()
    db.gallery_images.find.return_value = FakeCursor()
    db.site_settings.find_one = AsyncMock(return_value=None)
    db.site_settings.update_one = AsyncMock()

    with patch(
        "app.instagram_widget.get_instagram_widget_data",
        return_value={"profile": {"username": "aia_legnano"}, "posts": [], "stats": {}},
    ):
        with patch(
            "app.media_urls.resolve_media_fields",
            side_effect=lambda item: item.update(
                {"url": "https://site.test/uploads/ig1.jpg"}
            ),
        ):
            data = await build_instagram_widget_payload(db, "aia_legnano", limit=8)

    assert len(data["posts"]) == 1
    assert data["posts"][0]["imageUrl"].startswith("https://site.test/")


@pytest.mark.asyncio
async def test_build_widget_uses_mongo_cache_before_empty():
    class EmptyCursor:
        def sort(self, *_a, **_k):
            return self

        async def to_list(self, _limit):
            return []

    db = MagicMock()
    db.gallery_images.find.return_value = EmptyCursor()
    db.site_settings.find_one = AsyncMock(
        return_value={
            "id": "instagram-widget-cache",
            "profile": {"username": "aia_legnano", "fullName": "AIA"},
            "posts": [
                {
                    "shortcode": "Cached1",
                    "permalink": "https://www.instagram.com/p/Cached1/",
                    "imageUrl": "https://cdn.example/c.jpg",
                    "caption": "ok",
                }
            ],
            "updatedAt": "2026-01-01T00:00:00+00:00",
        }
    )
    db.site_settings.update_one = AsyncMock()

    with patch(
        "app.instagram_widget.get_instagram_widget_data",
        return_value={
            "profile": {"username": "aia_legnano"},
            "posts": [],
            "error": "Instagram feed HTTP 401",
            "stats": {},
        },
    ):
        data = await build_instagram_widget_payload(db, "aia_legnano", limit=9)

    assert len(data["posts"]) == 1
    assert data["posts"][0]["shortcode"] == "Cached1"
    assert data.get("fromCache") is True
    assert "error" not in data


@pytest.mark.asyncio
async def test_save_and_load_widget_cache_roundtrip():
    store: dict = {}

    async def update_one(filt, update, upsert=False):
        doc = store.get(filt["id"], {})
        doc.update(update.get("$set") or {})
        store[filt["id"]] = doc

    async def find_one(filt, proj=None):
        return store.get(filt["id"])

    db = MagicMock()
    db.site_settings.update_one = update_one
    db.site_settings.find_one = find_one

    await save_widget_cache(
        db,
        "aia_legnano",
        {
            "profile": {"username": "aia_legnano"},
            "posts": [{"shortcode": "P1", "imageUrl": "u", "permalink": "p"}],
        },
    )
    loaded = await load_widget_cache(db)
    assert loaded["posts"][0]["shortcode"] == "P1"
