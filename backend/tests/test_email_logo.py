"""Logo branding in outbound emails."""

import os

from app.mailer import (
    EMAIL_LOGO_CID,
    email_logo_attachment,
    email_logo_bytes,
    email_logo_img_src,
    email_logo_url,
    portal_frontend_url,
    render_contact_email,
    render_event_created_email,
    render_lead_confirmation_email,
    render_lead_email,
    wrap_email,
)


def test_email_logo_url_uses_portal_frontend(monkeypatch):
    monkeypatch.delenv("PUBLIC_API_URL", raising=False)
    monkeypatch.setenv("PORTAL_FRONTEND_URL", "https://aia-virid.vercel.app")
    assert email_logo_url() == (
        "https://aia-virid.vercel.app/brand/logo-aia-legnano-email.png"
    )
    assert portal_frontend_url() == "https://aia-virid.vercel.app"


def test_email_logo_url_prefers_public_api(monkeypatch):
    monkeypatch.setenv("PUBLIC_API_URL", "https://api.aia-legnano.it")
    assert email_logo_url() == "https://api.aia-legnano.it/api/public/email-logo.png"


def test_portal_frontend_url_ignores_localhost(monkeypatch):
    monkeypatch.setenv("PORTAL_FRONTEND_URL", "http://localhost:3000")
    assert portal_frontend_url() == "https://www.aia-legnano.it"


def test_wrap_email_uses_https_or_cid_logo(monkeypatch):
    monkeypatch.setenv("PORTAL_FRONTEND_URL", "https://example.test")
    html = wrap_email("<p>Ciao</p>")
    src = email_logo_img_src()
    assert f'src="{src}"' in html
    assert src.startswith("https://") or src.startswith("cid:")
    assert "Sezione AIA Legnano" in html
    assert "Ciao" in html
    assert 'alt="AIA Legnano"' in html


def test_email_logo_bytes_available():
    raw = email_logo_bytes()
    assert raw is not None and len(raw) > 100
    att = email_logo_attachment()
    assert att is not None
    assert att["content_id"] == EMAIL_LOGO_CID
    assert att["filename"].endswith(".png")
    assert att.get("content") or att.get("path")


def test_send_email_packs_path_attachment(monkeypatch):
    from app.mailer import send_email
    import asyncio

    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    captured = {}

    def fake_send(params):
        captured.update(params)
        return {"id": "test"}

    async def run():
        import resend

        resend.Emails.send = fake_send
        await send_email(
            "a@b.it",
            "Test",
            wrap_email("<p>Hi</p>"),
        )

    asyncio.run(run())
    atts = captured.get("attachments") or []
    assert atts
    logo_att = atts[0]
    assert logo_att.get("content_id") == EMAIL_LOGO_CID
    assert logo_att.get("content") or logo_att.get("path")


def test_templates_include_logo(monkeypatch):
    monkeypatch.setenv("PORTAL_FRONTEND_URL", "https://aia-virid.vercel.app")
    lead = render_lead_email(
        {
            "firstName": "A",
            "lastName": "B",
            "email": "a@b.it",
            "contactPreference": "email",
        }
    )
    contact = render_contact_email(
        {"name": "X", "email": "x@y.it", "subject": "Hi", "body": "Test"}
    )
    confirm = render_lead_confirmation_email(
        first_name="Mario", contact_preference="phone"
    )
    event = render_event_created_email(
        {
            "id": "1",
            "titolo": "Riunione",
            "date": "2026-09-15",
            "orario": "18:30",
            "luogo": "Sede",
        },
        {"firstName": "Simone", "lastName": "D"},
        link="https://aia-virid.vercel.app/area-associati/calendario",
    )
    for html in (lead, contact, confirm, event):
        assert "logo-aia-legnano" in html or f"cid:{EMAIL_LOGO_CID}" in html
        assert "Sezione AIA Legnano" in html
