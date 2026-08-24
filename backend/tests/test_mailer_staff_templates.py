"""Template email staff: testimonianze e foto galleria."""

from app.mailer import (
    DEFAULT_NOTIFY,
    notify_email,
    render_gallery_upload_staff_email,
    render_testimonial_staff_email,
)


class TestNotifyEmailDefault:
    def test_defaults_to_sezione(self, monkeypatch):
        monkeypatch.delenv("NOTIFY_EMAIL", raising=False)
        assert notify_email() == DEFAULT_NOTIFY
        assert notify_email() == "legnano@aia-figc.it"

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("NOTIFY_EMAIL", "segreteria@example.it")
        assert notify_email() == "segreteria@example.it"


class TestTestimonialStaffEmail:
    def test_includes_escaped_content(self):
        html = render_testimonial_staff_email(
            {
                "name": "Mario <Rossi>",
                "role": "Arbitro",
                "quote": "Sono orgoglioso & felice di far parte della sezione.",
            }
        )
        assert "Nuova testimonianza da approvare" in html
        assert "Mario &lt;Rossi&gt;" in html
        assert "Arbitro" in html
        assert "orgoglioso &amp; felice" in html
        assert "<script>" not in html


class TestGalleryUploadStaffEmail:
    def test_includes_fields_and_http_link(self):
        html = render_gallery_upload_staff_email(
            {
                "memberName": "Luca Bianchi",
                "caption": "Torneo <giovanile>",
                "category": "Eventi",
                "url": "https://cdn.example/foto.jpg",
            }
        )
        assert "Nuova foto galleria da approvare" in html
        assert "Luca Bianchi" in html
        assert "Torneo &lt;giovanile&gt;" in html
        assert "Eventi" in html
        assert 'href="https://cdn.example/foto.jpg"' in html

    def test_relative_url_has_no_link(self):
        html = render_gallery_upload_staff_email(
            {
                "memberName": "Anna",
                "caption": "",
                "category": "",
                "url": "/api/uploads/x.jpg",
            }
        )
        assert "Apri immagine" not in html
        assert "Anna" in html
