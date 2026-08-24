from unittest.mock import MagicMock, patch

from app.instagram_widget import (
    _merge_posts,
    build_instagram_widget_payload,
    fetch_instagram_widget_sync,
    get_instagram_widget_data,
)


def test_merge_posts_prefers_live_then_gallery():
    live = [{"shortcode": "A", "permalink": "https://instagram.com/p/A/", "imageUrl": "a"}]
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
                "image_versions2": {"candidates": [{"url": "https://cdn.example/post.jpg"}]},
            }
        ],
    }
    with patch("app.instagram_widget.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value.get.return_value = mock_response
        data = fetch_instagram_widget_sync("aia_legnano", limit=4)
    assert data["profile"]["username"] == "aia_legnano"
    assert len(data["posts"]) == 1
    assert data["posts"][0]["permalink"].endswith("/p/AbC123/")


async def test_get_instagram_widget_data_with_stats():
    data = await get_instagram_widget_data(
        "aia_legnano",
        limit=4,
        stats={"posts": 100, "followers": 1200, "following": 50},
    )
    assert data["stats"]["posts"] == 100
    assert data["stats"]["followers"] == 1200
    assert data["stats"]["following"] == 50


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

    with patch(
        "app.instagram_widget.get_instagram_widget_data",
        return_value={"profile": {"username": "aia_legnano"}, "posts": [], "stats": {}},
    ):
        with patch(
            "app.media_urls.resolve_media_fields",
            side_effect=lambda item: item.update({"url": "https://site.test/uploads/ig1.jpg"}),
        ):
            data = await build_instagram_widget_payload(db, "aia_legnano", limit=8)

    assert len(data["posts"]) == 1
    assert data["posts"][0]["imageUrl"].startswith("https://site.test/")
