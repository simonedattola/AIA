"""Backend integration tests for AIA Legnano platform.

Covers:
- Admin auth (login, /me, 401)
- Public endpoints (settings, nav, articles, events, officials, members, designations, stats)
- Public forms (corso-arbitri, contatti) - persistence
- Admin CRUD: articles (with HTML sanitization), events, officials, members, designations
- Admin lead/messages list + status update
- Admin settings PUT reflects in public GET
"""

import os
import time
import uuid

import pytest
import requests

pytestmark = pytest.mark.integration

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL", "https://arbitri-platform.preview.emergentagent.com"
).rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@aia-legnano.it")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")


# ---------- Fixtures ----------
@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def admin_token(session):
    r = session.post(
        f"{API}/admin/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    data = r.json()
    assert (
        "token" in data and isinstance(data["token"], str) and len(data["token"]) > 10
    )
    assert data["admin"]["email"] == ADMIN_EMAIL
    return data["token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }


# ---------- Health ----------
def test_health_root(session):
    r = session.get(f"{API}/", timeout=10)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


# ---------- Admin Auth ----------
class TestAdminAuth:
    def test_login_success(self, session):
        r = session.post(
            f"{API}/admin/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["admin"]["email"] == ADMIN_EMAIL
        assert "name" in body["admin"]
        assert isinstance(body["token"], str)

    def test_login_invalid(self, session):
        r = session.post(
            f"{API}/admin/login", json={"email": ADMIN_EMAIL, "password": "wrong"}
        )
        assert r.status_code == 401

    def test_me_with_token(self, session, admin_headers):
        r = session.get(f"{API}/admin/me", headers=admin_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == ADMIN_EMAIL
        assert "name" in body

    def test_me_without_token(self, session):
        # plain requests session has no auth header, but session fixture sets Content-Type
        r = requests.get(f"{API}/admin/me")
        assert r.status_code == 401

    def test_dashboard(self, session, admin_headers):
        r = session.get(f"{API}/admin/dashboard", headers=admin_headers)
        assert r.status_code == 200
        body = r.json()
        for key in [
            "articles",
            "events",
            "members",
            "designations",
            "leadsTotal",
            "messagesTotal",
        ]:
            assert key in body
            assert isinstance(body[key], int)


# ---------- Public endpoints ----------
class TestPublic:
    def test_settings(self, session):
        r = session.get(f"{API}/public/settings")
        assert r.status_code == 200
        body = r.json()
        assert "siteName" in body
        assert "phone" in body
        assert "email" in body

    def test_nav(self, session):
        r = session.get(f"{API}/public/nav")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list) and len(items) > 0
        # ordering
        orders = [i.get("order", 0) for i in items]
        assert orders == sorted(orders)

    def test_articles_list(self, session):
        r = session.get(f"{API}/public/articles?limit=20")
        assert r.status_code == 200
        body = r.json()
        assert "items" in body and "total" in body
        assert body["total"] >= 9
        assert len(body["items"]) >= 1

    def test_article_detail(self, session):
        slug = "approfondimento-dogso-spa"
        r = session.get(f"{API}/public/articles/{slug}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "article" in body and "related" in body
        assert body["article"]["slug"] == slug
        assert isinstance(body["related"], list)

    def test_article_detail_404(self, session):
        r = session.get(f"{API}/public/articles/non-esiste-slug-xxx")
        assert r.status_code == 404

    def test_categories(self, session):
        r = session.get(f"{API}/public/categories")
        assert r.status_code == 200
        cats = r.json()
        assert isinstance(cats, list) and len(cats) >= 1

    def test_events_upcoming(self, session):
        r = session.get(f"{API}/public/events?upcoming=true")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        from datetime import datetime, timezone

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        for ev in items:
            assert ev["date"] >= today, f"upcoming filter failed: {ev}"

    def test_officials(self, session):
        r = session.get(f"{API}/public/officials")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        assert len(items) >= 7
        # sorted by sortOrder asc
        orders = [i.get("sortOrder", 0) for i in items]
        assert orders == sorted(orders)

    def test_members_filter(self, session):
        r = session.get(f"{API}/public/members?scope=organigramma")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        for m in items:
            assert m["kind"] in ("oa", "ot", "osservatore")

    def test_members_default_excludes_observers(self, session):
        r_arb = session.get(f"{API}/public/members")
        if r_arb.status_code != 200:
            pytest.skip("members API unavailable")
        for m in r_arb.json():
            assert m["kind"] in ("associato", "tutor")

    def test_member_detail(self, session):
        # get first member
        r = session.get(f"{API}/public/members")
        members = r.json()
        if not members:
            pytest.skip("No members seeded")
        slug = members[0]["slug"]
        r2 = session.get(f"{API}/public/members/{slug}")
        assert r2.status_code == 200
        body = r2.json()
        assert "member" in body and "designations" in body
        assert body["member"]["slug"] == slug

    def test_designations_role_filter(self, session):
        r = session.get(f"{API}/public/designations?role=Arbitro")
        assert r.status_code == 200
        items = r.json()
        for d in items:
            assert d["role"] == "Arbitro"

    def test_stats(self, session):
        r = session.get(f"{API}/public/stats")
        assert r.status_code == 200
        body = r.json()
        for key in [
            "members",
            "articles",
            "matchesThisSeason",
            "activeSeason",
            "eventsUpcoming",
            "yearsActive",
            "foundedYear",
        ]:
            assert key in body


# ---------- Forms ----------
class TestForms:
    def test_lead_create_and_appears_in_admin(self, session, admin_headers):
        unique = uuid.uuid4().hex[:8]
        payload = {
            "firstName": "TEST",
            "lastName": f"User{unique}",
            "email": f"test_{unique}@example.com",
            "age": 18,
            "phone": "3331234567",
            "contactPreference": "email",
            "message": "Test automatico",
        }
        r = session.post(f"{API}/public/forms/corso-arbitri", json=payload)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["ok"] is True
        lead_id = body["id"]
        assert isinstance(lead_id, str)

        # appears in admin list
        r2 = session.get(f"{API}/admin/leads", headers=admin_headers)
        assert r2.status_code == 200
        leads = r2.json()
        found = next((l for l in leads if l["id"] == lead_id), None)
        assert found is not None, "lead not visible in admin list"
        assert found["status"] == "new"
        assert found["email"] == payload["email"]

        # update status
        r3 = session.put(
            f"{API}/admin/leads/{lead_id}",
            headers=admin_headers,
            json={"status": "contacted"},
        )
        assert r3.status_code == 200
        # verify
        r4 = session.get(f"{API}/admin/leads", headers=admin_headers)
        updated = next((l for l in r4.json() if l["id"] == lead_id), None)
        assert updated and updated["status"] == "contacted"

        # cleanup
        session.delete(f"{API}/admin/leads/{lead_id}", headers=admin_headers)

    def test_contact_create(self, session, admin_headers):
        unique = uuid.uuid4().hex[:8]
        payload = {
            "name": f"TEST Mario {unique}",
            "email": f"contact_{unique}@example.com",
            "subject": "Test subject",
            "body": "Test body",
        }
        r = session.post(f"{API}/public/forms/contatti", json=payload)
        assert r.status_code == 201
        body = r.json()
        assert body["ok"] is True
        msg_id = body["id"]
        # verify it exists in admin
        r2 = session.get(f"{API}/admin/messages", headers=admin_headers)
        assert r2.status_code == 200
        found = next((m for m in r2.json() if m["id"] == msg_id), None)
        assert found is not None
        # cleanup
        session.delete(f"{API}/admin/messages/{msg_id}", headers=admin_headers)


# ---------- Admin CRUD: articles + HTML sanitization ----------
class TestAdminArticles:
    created_id = None

    def test_create_article_with_script_sanitized(self, session, admin_headers):
        unique = uuid.uuid4().hex[:8]
        payload = {
            "title": f"TEST articolo {unique}",
            "category": "Vita sezionale",
            "excerpt": "Test excerpt",
            "bodyHtml": "<p>Hello</p><script>alert(1)</script><p>World</p>",
            "status": "published",
        }
        r = session.post(f"{API}/admin/articles", headers=admin_headers, json=payload)
        assert r.status_code == 200, r.text
        art = r.json()
        assert "id" in art
        # Sanitization must strip the <script> tag (inner text may be preserved as plain text)
        assert "<script" not in art["bodyHtml"].lower()
        assert "</script" not in art["bodyHtml"].lower()
        assert "<p>Hello</p>" in art["bodyHtml"]
        assert "<p>World</p>" in art["bodyHtml"]
        TestAdminArticles.created_id = art["id"]
        TestAdminArticles.created_slug = art["slug"]

    def test_get_article_via_public(self, session):
        if not TestAdminArticles.created_id:
            pytest.skip("create failed")
        r = session.get(f"{API}/public/articles/{TestAdminArticles.created_slug}")
        assert r.status_code == 200

    def test_update_article(self, session, admin_headers):
        if not TestAdminArticles.created_id:
            pytest.skip("create failed")
        # fetch first
        r = session.get(
            f"{API}/admin/articles/{TestAdminArticles.created_id}",
            headers=admin_headers,
        )
        assert r.status_code == 200
        art = r.json()
        art["title"] = art["title"] + " UPDATED"
        r2 = session.put(
            f"{API}/admin/articles/{TestAdminArticles.created_id}",
            headers=admin_headers,
            json=art,
        )
        assert r2.status_code == 200
        assert "UPDATED" in r2.json()["title"]

    def test_delete_article(self, session, admin_headers):
        if not TestAdminArticles.created_id:
            pytest.skip("create failed")
        r = session.delete(
            f"{API}/admin/articles/{TestAdminArticles.created_id}",
            headers=admin_headers,
        )
        assert r.status_code == 200
        # verify gone
        r2 = session.get(
            f"{API}/admin/articles/{TestAdminArticles.created_id}",
            headers=admin_headers,
        )
        assert r2.status_code == 404


# ---------- Admin CRUD: events, officials, members, designations ----------
class TestAdminMisc:
    def test_event_crud(self, session, admin_headers):
        payload = {
            "date": "2030-01-15",
            "titolo": "TEST evento",
            "descrizione": "x",
            "luogo": "Legnano",
            "tipo": "riunione",
        }
        r = session.post(f"{API}/admin/events", headers=admin_headers, json=payload)
        assert r.status_code == 200, r.text
        ev = r.json()
        eid = ev["id"]
        # update
        ev["titolo"] = "TEST evento UPDATED"
        r2 = session.put(f"{API}/admin/events/{eid}", headers=admin_headers, json=ev)
        assert r2.status_code == 200
        # delete
        r3 = session.delete(f"{API}/admin/events/{eid}", headers=admin_headers)
        assert r3.status_code == 200

    def test_official_crud(self, session, admin_headers):
        payload = {
            "role": "TEST role",
            "firstName": "TEST",
            "lastName": "Person",
            "sortOrder": 99,
        }
        r = session.post(f"{API}/admin/officials", headers=admin_headers, json=payload)
        assert r.status_code == 200, r.text
        off = r.json()
        oid = off["id"]
        off["role"] = "TEST role UPDATED"
        r2 = session.put(
            f"{API}/admin/officials/{oid}", headers=admin_headers, json=off
        )
        assert r2.status_code == 200
        r3 = session.delete(f"{API}/admin/officials/{oid}", headers=admin_headers)
        assert r3.status_code == 200

    def test_member_crud(self, session, admin_headers):
        unique = uuid.uuid4().hex[:6]
        payload = {
            "slug": f"test-member-{unique}",
            "firstName": "TESTm",
            "lastName": f"Person{unique}",
            "kind": "associato",
            "role": "Arbitro",
        }
        r = session.post(f"{API}/admin/members", headers=admin_headers, json=payload)
        assert r.status_code == 200, r.text
        m = r.json()
        mid = m["id"]
        m["role"] = "Assistente"
        r2 = session.put(f"{API}/admin/members/{mid}", headers=admin_headers, json=m)
        assert r2.status_code == 200
        r3 = session.delete(f"{API}/admin/members/{mid}", headers=admin_headers)
        assert r3.status_code == 200

    def test_designation_crud(self, session, admin_headers):
        payload = {
            "matchDate": "2030-02-10",
            "matchLabel": "TEST match",
            "role": "Arbitro",
            "status": "published",
        }
        r = session.post(
            f"{API}/admin/designations", headers=admin_headers, json=payload
        )
        assert r.status_code == 200, r.text
        d = r.json()
        did = d["id"]
        d["matchLabel"] = "TEST match UPDATED"
        r2 = session.put(
            f"{API}/admin/designations/{did}", headers=admin_headers, json=d
        )
        assert r2.status_code == 200
        r3 = session.delete(f"{API}/admin/designations/{did}", headers=admin_headers)
        assert r3.status_code == 200


# ---------- Settings PUT round-trip ----------
class TestAdminSettings:
    def test_settings_update_reflects_in_public(self, session, admin_headers):
        # get current
        r = session.get(f"{API}/admin/settings", headers=admin_headers)
        assert r.status_code == 200
        current = r.json()
        original_phone = current.get("phone", "+39 0331 000000")
        # change phone
        new_phone = f"+39 0331 {uuid.uuid4().hex[:6]}"
        current["phone"] = new_phone
        r2 = session.put(f"{API}/admin/settings", headers=admin_headers, json=current)
        assert r2.status_code == 200
        # verify in public
        time.sleep(0.3)
        r3 = session.get(f"{API}/public/settings")
        assert r3.status_code == 200
        assert r3.json().get("phone") == new_phone
        # restore
        current["phone"] = original_phone
        session.put(f"{API}/admin/settings", headers=admin_headers, json=current)
