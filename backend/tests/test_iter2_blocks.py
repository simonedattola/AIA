"""Iteration 2 backend tests - Block-based CMS (Pages, Testimonials, Documents)."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"
ADMIN_EMAIL = "admin@aia-legnano.it"
ADMIN_PASSWORD = "AiaLegnano2026!"


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def admin_headers(session):
    r = session.post(f"{API}/admin/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------- Public Pages with blocks ----------
class TestPublicPagesBlocks:
    def test_home_page_blocks(self, session):
        r = session.get(f"{API}/public/pages/home")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["slug"] == "home"
        assert isinstance(body["blocks"], list)
        types = [b["type"] for b in body["blocks"]]
        # Required block types for home
        for t in ["hero", "news_slider", "events_list", "cta"]:
            assert t in types, f"home blocks missing {t}: {types}"
        assert len(body["blocks"]) == 4

    def test_diventa_arbitro_page_blocks(self, session):
        r = session.get(f"{API}/public/pages/diventa-arbitro")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["slug"] == "diventa-arbitro"
        types = [b["type"] for b in body["blocks"]]
        for t in ["hero", "text_image", "stats", "timeline", "testimonials", "cta", "faq"]:
            assert t in types, f"diventa-arbitro blocks missing {t}: {types}"
        assert len(body["blocks"]) == 7

    def test_testimonials_seeded(self, session):
        r = session.get(f"{API}/public/testimonials")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list) and len(items) >= 3
        names = {t["name"] for t in items}
        for n in ["Francesca Conti", "Matteo Colombo", "Elena Sala"]:
            assert n in names, f"missing testimonial {n}: {names}"

    def test_documents_seeded(self, session):
        r = session.get(f"{API}/public/documents")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list) and len(items) >= 3


# ---------- Admin Pages CRUD ----------
class TestAdminPages:
    def test_list_pages_includes_system(self, session, admin_headers):
        r = session.get(f"{API}/admin/pages", headers=admin_headers)
        assert r.status_code == 200
        pages = r.json()
        slugs = {p["slug"] for p in pages}
        assert "home" in slugs
        assert "diventa-arbitro" in slugs

    def test_get_page_home(self, session, admin_headers):
        # Find home id from list
        r = session.get(f"{API}/admin/pages", headers=admin_headers)
        home = next((p for p in r.json() if p["slug"] == "home"), None)
        assert home is not None
        r2 = session.get(f"{API}/admin/pages/{home['id']}", headers=admin_headers)
        assert r2.status_code == 200
        body = r2.json()
        assert isinstance(body["blocks"], list)
        assert len(body["blocks"]) == 4

    def test_update_page_modifies_block_and_reflects_public(self, session, admin_headers):
        r = session.get(f"{API}/admin/pages", headers=admin_headers)
        home = next(p for p in r.json() if p["slug"] == "home")
        page_id = home["id"]
        # Modify hero block title
        full = session.get(f"{API}/admin/pages/{page_id}", headers=admin_headers).json()
        original_title = full["blocks"][0].get("config", {}).get("title", "")
        new_title = f"TEST Hero {uuid.uuid4().hex[:6]}"
        full["blocks"][0].setdefault("config", {})["title"] = new_title
        r2 = session.put(f"{API}/admin/pages/{page_id}", headers=admin_headers, json=full)
        assert r2.status_code == 200, r2.text
        # Public reflects
        r3 = session.get(f"{API}/public/pages/home")
        assert r3.json()["blocks"][0]["config"]["title"] == new_title
        # Restore
        full["blocks"][0]["config"]["title"] = original_title
        session.put(f"{API}/admin/pages/{page_id}", headers=admin_headers, json=full)

    def test_reorder_blocks(self, session, admin_headers):
        r = session.get(f"{API}/admin/pages", headers=admin_headers)
        home = next(p for p in r.json() if p["slug"] == "home")
        page_id = home["id"]
        full = session.get(f"{API}/admin/pages/{page_id}", headers=admin_headers).json()
        original_order = [b["type"] for b in full["blocks"]]
        reversed_blocks = list(reversed(full["blocks"]))
        full["blocks"] = reversed_blocks
        r2 = session.put(f"{API}/admin/pages/{page_id}", headers=admin_headers, json=full)
        assert r2.status_code == 200
        r3 = session.get(f"{API}/public/pages/home")
        new_order = [b["type"] for b in r3.json()["blocks"]]
        assert new_order == list(reversed(original_order)), f"expected reversed; got {new_order}"
        # Restore
        full["blocks"] = list(reversed(reversed_blocks))
        session.put(f"{API}/admin/pages/{page_id}", headers=admin_headers, json=full)

    def test_rich_text_sanitization(self, session, admin_headers):
        # Create custom page, add rich_text block with script, expect script stripped
        unique = uuid.uuid4().hex[:8]
        payload = {
            "slug": f"test-rt-{unique}",
            "title": f"TEST RT {unique}",
            "blocks": [
                {"id": "b1", "type": "rich_text",
                 "config": {"html": "<p>ok</p><script>alert(1)</script>"}}
            ],
        }
        r = session.post(f"{API}/admin/pages", headers=admin_headers, json=payload)
        assert r.status_code == 200, r.text
        page = r.json()
        pid = page["id"]
        html = page["blocks"][0]["config"]["html"].lower()
        assert "<script" not in html and "</script" not in html
        assert "<p>ok</p>" in page["blocks"][0]["config"]["html"]
        # Test on PUT too
        page["blocks"][0]["config"]["html"] = "<p>fine</p><script>bad()</script>"
        r2 = session.put(f"{API}/admin/pages/{pid}", headers=admin_headers, json=page)
        assert r2.status_code == 200
        html2 = r2.json()["blocks"][0]["config"]["html"].lower()
        assert "<script" not in html2
        # cleanup
        session.delete(f"{API}/admin/pages/{pid}", headers=admin_headers)

    def test_create_and_public_lookup_custom_page(self, session, admin_headers):
        unique = uuid.uuid4().hex[:6]
        title = f"TEST Arbitri Platform {unique}"
        # Create using title-derived slug auto
        payload = {"slug": "", "title": title, "blocks": [], "status": "published"}
        r = session.post(f"{API}/admin/pages", headers=admin_headers, json=payload)
        assert r.status_code == 200, r.text
        page = r.json()
        assert page["slug"]  # auto-generated
        # Public lookup
        r2 = session.get(f"{API}/public/pages/{page['slug']}")
        assert r2.status_code == 200
        # cleanup
        session.delete(f"{API}/admin/pages/{page['id']}", headers=admin_headers)

    def test_delete_system_page_forbidden(self, session, admin_headers):
        r = session.get(f"{API}/admin/pages", headers=admin_headers)
        home = next(p for p in r.json() if p["slug"] == "home")
        r2 = session.delete(f"{API}/admin/pages/{home['id']}", headers=admin_headers)
        assert r2.status_code == 400

    def test_delete_custom_page_ok(self, session, admin_headers):
        unique = uuid.uuid4().hex[:6]
        payload = {"slug": f"test-del-{unique}", "title": f"TEST Del {unique}", "blocks": []}
        r = session.post(f"{API}/admin/pages", headers=admin_headers, json=payload)
        pid = r.json()["id"]
        r2 = session.delete(f"{API}/admin/pages/{pid}", headers=admin_headers)
        assert r2.status_code == 200

    def test_show_in_menu_page_in_nav(self, session, admin_headers):
        unique = uuid.uuid4().hex[:6]
        payload = {
            "slug": f"test-menu-{unique}",
            "title": f"TEST Menu {unique}",
            "blocks": [],
            "status": "published",
            "showInMenu": True,
            "menuLabel": f"TestMenu{unique}",
            "menuOrder": 99,
        }
        r = session.post(f"{API}/admin/pages", headers=admin_headers, json=payload)
        assert r.status_code == 200, r.text
        page = r.json()
        # Nav should include this page
        r2 = session.get(f"{API}/public/nav")
        assert r2.status_code == 200
        items = r2.json()
        labels = {i["label"] for i in items}
        hrefs = {i["href"] for i in items}
        assert page["menuLabel"] in labels, f"menu label not in nav: {labels}"
        assert f"/p/{page['slug']}" in hrefs
        # cleanup
        session.delete(f"{API}/admin/pages/{page['id']}", headers=admin_headers)


# ---------- Documents CRUD ----------
class TestAdminDocuments:
    def test_document_crud_flow(self, session, admin_headers):
        unique = uuid.uuid4().hex[:6]
        payload = {
            "title": f"TEST Doc {unique}",
            "description": "tmp",
            "fileUrl": "https://example.com/x.pdf",
            "category": "modulistica",
            "sortOrder": 50,
        }
        r = session.post(f"{API}/admin/documents", headers=admin_headers, json=payload)
        assert r.status_code == 200, r.text
        doc = r.json()
        did = doc["id"]
        # admin list
        r2 = session.get(f"{API}/admin/documents", headers=admin_headers)
        assert any(d["id"] == did for d in r2.json())
        # public list
        r3 = session.get(f"{API}/public/documents")
        assert any(d["id"] == did for d in r3.json())
        # delete
        r4 = session.delete(f"{API}/admin/documents/{did}", headers=admin_headers)
        assert r4.status_code == 200
        r5 = session.get(f"{API}/admin/documents", headers=admin_headers)
        assert not any(d["id"] == did for d in r5.json())


# ---------- Testimonials CRUD ----------
class TestAdminTestimonials:
    def test_testimonial_crud_flow(self, session, admin_headers):
        unique = uuid.uuid4().hex[:6]
        payload = {
            "name": f"TEST Person {unique}",
            "role": "Arbitro",
            "quote": "frase di test",
            "sortOrder": 50,
        }
        r = session.post(f"{API}/admin/testimonials", headers=admin_headers, json=payload)
        assert r.status_code == 200, r.text
        t = r.json()
        tid = t["id"]
        r2 = session.get(f"{API}/admin/testimonials", headers=admin_headers)
        assert any(x["id"] == tid for x in r2.json())
        r3 = session.get(f"{API}/public/testimonials")
        assert any(x["id"] == tid for x in r3.json())
        r4 = session.delete(f"{API}/admin/testimonials/{tid}", headers=admin_headers)
        assert r4.status_code == 200
