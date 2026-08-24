"""Logo branding in outbound emails."""

import os

from app.mailer import (
    email_logo_url,
    portal_frontend_url,
    render_contact_email,
    render_event_created_email,
    render_lead_confirmation_email,
    render_lead_email,
    wrap_email,
)


def test_email_logo_url_uses_portal_frontend(monkeypatch):
    monkeypatch.setenv("PORTAL_FRONTEND_URL", "https://aia-virid.vercel.app")
    assert email_logo_url() == (
        "https://aia-virid.vercel.app/brand/logo-aia-legnano-email.png"
    )
    assert portal_frontend_url() == "https://aia-virid.vercel.app"


def test_wrap_email_includes_logo_and_section_name(monkeypatch):
    monkeypatch.setenv("PORTAL_FRONTEND_URL", "https://example.test")
    html = wrap_email("<p>Ciao</p>")
    assert "logo-aia-legnano-email.png" in html
    assert "Sezione AIA Legnano" in html
    assert "Ciao" in html
    assert 'alt="AIA Legnano"' in html


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
        assert "logo-aia-legnano-email.png" in html
        assert "Sezione AIA Legnano" in html
