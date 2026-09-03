"""Tests for designations scheduler interval and catch-up."""

from datetime import datetime, timezone, timedelta

from app.designations_scheduler import (
    DEFAULT_INTERVAL_HOURS,
    interval_hours,
    seconds_until_due,
)


def test_default_interval_is_six_hours(monkeypatch):
    monkeypatch.delenv("DESIGNATIONS_SYNC_INTERVAL_HOURS", raising=False)
    assert DEFAULT_INTERVAL_HOURS == 6.0
    assert interval_hours() == 6.0


def test_interval_hours_from_env(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_SYNC_INTERVAL_HOURS", "6")
    assert interval_hours() == 6.0


def test_seconds_until_due_overdue_when_never_ran():
    assert seconds_until_due(None, interval_sec=6 * 3600) == 0.0


def test_seconds_until_due_overdue_after_week():
    now = datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)
    last = (now - timedelta(days=7)).isoformat()
    assert seconds_until_due(last, now=now, interval_sec=6 * 3600) == 0.0


def test_seconds_until_due_remaining_within_interval():
    now = datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)
    last = (now - timedelta(hours=2)).isoformat()
    wait = seconds_until_due(last, now=now, interval_sec=6 * 3600)
    assert abs(wait - 4 * 3600) < 1
