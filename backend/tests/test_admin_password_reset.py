"""Reset password amministratore."""

import pytest

from app.admin_password_reset import (
    _hash_token,
    request_admin_password_reset,
    reset_admin_password,
)
from app.security import hash_password, verify_password


class _FakeInsertResult:
    inserted_id = "x"


class _FakeResets:
    def __init__(self):
        self.docs = []

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items() if not k.startswith("$")):
                if "createdAt" in query and "$gte" in query["createdAt"]:
                    if doc.get("createdAt", "") < query["createdAt"]["$gte"]:
                        continue
                if doc.get("usedAt") is None and query.get("usedAt") is None:
                    return doc
                if doc.get("usedAt") == query.get("usedAt"):
                    return doc
            if doc.get("tokenHash") == query.get("tokenHash") and query.get("usedAt") is None:
                if doc.get("usedAt") is None:
                    return doc
        for doc in self.docs:
            if doc.get("tokenHash") == query.get("tokenHash") and doc.get("usedAt") is None:
                return doc
        return None

    async def insert_one(self, doc):
        self.docs.append(doc.copy())
        return _FakeInsertResult()

    async def update_one(self, query, update):
        for doc in self.docs:
            if doc.get("id") == query.get("id"):
                doc.update(update.get("$set", {}))
                return

    async def update_many(self, query, update):
        for doc in self.docs:
            if doc.get("email") == query.get("email") and doc.get("usedAt") is None:
                if doc.get("id") != query.get("id", {}).get("$ne"):
                    doc.update(update.get("$set", {}))


class _FakeAdmins:
    def __init__(self, admin):
        self.admin = admin

    async def find_one(self, query, projection=None):
        email = query.get("email")
        if email and self.admin and self.admin.get("email") == email:
            return self.admin.copy()
        return None

    async def update_one(self, query, update):
        if self.admin and self.admin.get("email") == query.get("email"):
            self.admin.update(update.get("$set", {}))


class _FakeDb:
    def __init__(self, admin):
        self.admin_users = _FakeAdmins(admin)
        self.admin_password_resets = _FakeResets()


@pytest.mark.asyncio
async def test_reset_admin_password_updates_hash(monkeypatch):
    admin = {
        "id": "admin-root",
        "email": "legnano@aia-figc.it",
        "passwordHash": hash_password("vecchia-password"),
        "name": "Admin",
    }
    db = _FakeDb(admin)
    monkeypatch.setattr("app.admin_password_reset.get_db", lambda: db)

    raw = "test-token-abc12345678901234567890"
    db.admin_password_resets.docs.append(
        {
            "id": "r1",
            "email": admin["email"],
            "tokenHash": _hash_token(raw),
            "expiresAt": "2099-01-01T00:00:00+00:00",
            "createdAt": "2026-01-01T00:00:00+00:00",
            "usedAt": None,
        }
    )

    await reset_admin_password(raw, "nuova-password-sicura")
    assert verify_password("nuova-password-sicura", db.admin_users.admin["passwordHash"])
    assert db.admin_password_resets.docs[0]["usedAt"] is not None


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_is_silent(monkeypatch):
    db = _FakeDb(None)
    monkeypatch.setattr("app.admin_password_reset.get_db", lambda: db)
    sent = []

    async def fake_send(*args, **kwargs):
        sent.append(args)
        return True

    monkeypatch.setattr("app.admin_password_reset.send_email", fake_send)
    ok = await request_admin_password_reset("unknown@example.it")
    assert ok is True
    assert sent == []


@pytest.mark.asyncio
async def test_forgot_password_sends_for_admin(monkeypatch):
    admin = {"email": "legnano@aia-figc.it", "name": "Sezione"}
    db = _FakeDb(admin)
    monkeypatch.setattr("app.admin_password_reset.get_db", lambda: db)
    sent = []

    async def fake_send(to, subject, html):
        sent.append((to, subject))
        return True

    monkeypatch.setattr("app.admin_password_reset.send_email", fake_send)
    ok = await request_admin_password_reset(admin["email"])
    assert ok is True
    assert len(sent) == 1
    assert sent[0][0] == admin["email"]
