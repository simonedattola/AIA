"""HTML email escaping."""
from app.mailer import render_lead_email, render_contact_email


def test_lead_email_escapes_html():
    html = render_lead_email({
        "firstName": '<script>alert(1)</script>',
        "lastName": "Rossi&Co",
        "age": 20,
        "phone": "123",
        "email": "a@b.it",
        "contactPreference": "email",
        "message": "<b>hi</b>",
    })
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "Rossi&amp;Co" in html
    assert "&lt;b&gt;hi&lt;/b&gt;" in html


def test_contact_email_escapes_html():
    html = render_contact_email({
        "name": "<img src=x onerror=alert(1)>",
        "email": "a@b.it",
        "subject": "Ciao\"",
        "body": "line1\n<script>",
    })
    assert "<script>" not in html
    assert "&lt;img" in html
