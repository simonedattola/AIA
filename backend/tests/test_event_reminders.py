"""Tests for event email reminders."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.event_reminders import (
    EVENT_REMINDER_LEAD_HOURS,
    event_start_datetime,
    lead_hours_label,
    normalize_event_time,
)

ROME = ZoneInfo("Europe/Rome")


class TestNormalizeEventTime:
    def test_default(self):
        assert normalize_event_time("") == "09:00"
        assert normalize_event_time(None) == "09:00"

    def test_valid(self):
        assert normalize_event_time("14:30") == "14:30"
        assert normalize_event_time("9:05") == "09:05"
        # Minuti devono essere a 2 cifre; altrimenti fallback orario default
        assert normalize_event_time("9:5") == "09:00"


class TestEventStartDatetime:
    def test_combines_date_and_time(self):
        ev = {"date": "2026-06-15", "orario": "18:30"}
        dt = event_start_datetime(ev)
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 6
        assert dt.day == 15
        assert dt.hour == 18
        assert dt.minute == 30
        assert dt.tzinfo == ROME


class TestLeadHours:
    def test_options(self):
        assert EVENT_REMINDER_LEAD_HOURS == (24, 12, 6, 1)

    def test_label(self):
        assert lead_hours_label(24) == "24 ore prima"
        assert lead_hours_label(1) == "1 ora prima"
