"""Casella sezione per notifiche staff."""

import pytest

from app.staff_email import staff_notify_email


class _FakeCollection:
    def __init__(self, doc):
        self._doc = doc

    async def find_one(self, query, projection=None):
        return self._doc


class _FakeDb:
    def __init__(self, email: str):
        self.site_settings = _FakeCollection({"email": email} if email else None)


class TestStaffNotifyEmail:
    @pytest.mark.asyncio
    async def test_prefers_site_settings(self, monkeypatch):
        monkeypatch.setenv("NOTIFY_EMAIL", "altro@example.it")
        db = _FakeDb("legnano@aia-figc.it")
        assert await staff_notify_email(db) == "legnano@aia-figc.it"

    @pytest.mark.asyncio
    async def test_falls_back_to_env(self, monkeypatch):
        monkeypatch.setenv("NOTIFY_EMAIL", "segreteria@example.it")
        db = _FakeDb("")
        assert await staff_notify_email(db) == "segreteria@example.it"

    @pytest.mark.asyncio
    async def test_falls_back_to_default(self, monkeypatch):
        monkeypatch.delenv("NOTIFY_EMAIL", raising=False)
        db = _FakeDb("")
        assert await staff_notify_email(db) == "legnano@aia-figc.it"
