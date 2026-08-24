"""Tests for ICS / Google Calendar export."""

from datetime import timedelta
from zoneinfo import ZoneInfo

from app.event_ics import (
    build_ics,
    google_calendar_url,
    ics_filename,
    ics_uid,
)

SAMPLE = {
    "id": "evt-123",
    "titolo": "Riunione tecnica",
    "date": "2026-09-15",
    "orario": "18:30",
    "luogo": "Sede AIA Legnano",
    "descrizione": "Portare regolamento;\npresenza obbligatoria.",
}


class TestBuildIcs:
    def test_contains_vevent_and_fields(self):
        ics = build_ics(SAMPLE)
        assert ics is not None
        assert "BEGIN:VCALENDAR" in ics
        assert "BEGIN:VEVENT" in ics
        assert "SUMMARY:Riunione tecnica" in ics
        assert "LOCATION:Sede AIA Legnano" in ics
        assert "TZID=Europe/Rome" in ics
        assert "DTSTART;TZID=Europe/Rome:20260915T183000" in ics
        # default 2h duration
        assert "DTEND;TZID=Europe/Rome:20260915T203000" in ics
        assert ics_uid(SAMPLE) in ics
        assert "Portare regolamento" in ics

    def test_escapes_special_chars(self):
        ics = build_ics({**SAMPLE, "titolo": "A;B,C"})
        assert "SUMMARY:A\\;B\\,C" in ics

    def test_invalid_date(self):
        assert build_ics({**SAMPLE, "date": ""}) is None


class TestGoogleUrl:
    def test_template_url(self):
        url = google_calendar_url(SAMPLE)
        assert url.startswith("https://calendar.google.com/calendar/render?")
        assert "action=TEMPLATE" in url
        assert "Riunione" in url
        assert "ctz=Europe%2FRome" in url or "ctz=Europe/Rome" in url

    def test_filename(self):
        name = ics_filename(SAMPLE)
        assert name.endswith(".ics")
        assert "20260915" in name
        assert (
            "Riunione" in name
            or "riunione" in name.lower()
            or "tecnica" in name.lower()
        )
