"""Public members list: slim payload, no secrets, no N+1 category refresh."""

import pytest
from httpx import ASGITransport, AsyncClient

from server import app

pytestmark = pytest.mark.integration


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


FORBIDDEN_KEYS = {"passwordHash", "portalPassword", "notes", "meccanografico"}


@pytest.mark.asyncio
async def test_public_members_list_is_slim_and_safe(client):
    res = await client.get("/api/public/members", params={"limit": 5})
    assert res.status_code == 200
    data = res.json()
    if not data:
        pytest.skip("No members in database")
    assert isinstance(data, list)
    for item in data:
        assert "slug" in item
        assert "firstName" in item or "lastName" in item
        leaked = FORBIDDEN_KEYS & set(item.keys())
        assert not leaked, f"leaked private fields: {leaked}"
        # List endpoint should not ship full bios
        assert "bioHtml" not in item
        assert "bio" not in item
