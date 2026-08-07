"""Member public profile API."""

import pytest
from httpx import ASGITransport, AsyncClient

from server import app

pytestmark = pytest.mark.integration


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_member_profile_shape(client):
    members = await client.get("/api/public/members", params={"limit": 1})
    if members.status_code != 200 or not members.json():
        pytest.skip("No members in database")
    slug = members.json()[0]["slug"]
    res = await client.get(f"/api/public/members/{slug}")
    assert res.status_code == 200
    data = res.json()
    assert "member" in data
    assert "designations" in data
    assert "articles" in data
    assert "events" in data
    assert "testimonials" in data
    assert "awards" in data
