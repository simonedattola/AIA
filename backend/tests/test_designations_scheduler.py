"""Tests for designations scheduler interval, catch-up, and watchdog."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.designations_scheduler import (
    DEFAULT_INTERVAL_HOURS,
    ensure_scheduler_alive,
    interval_hours,
    maybe_run_overdue_sync,
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


@pytest.mark.asyncio
async def test_maybe_run_overdue_starts_when_due(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_AUTO_SYNC", "true")
    with (
        patch("app.designations_scheduler.ensure_scheduler_alive", return_value=True),
        patch(
            "app.designations_scheduler._last_success_at",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.designations_scheduler.start_sync_background", return_value=True
        ) as start,
    ):
        out = await maybe_run_overdue_sync(trigger="watchdog")
    assert out["started"] is True
    assert out["reason"] == "overdue"
    start.assert_called_once_with("watchdog")


@pytest.mark.asyncio
async def test_maybe_run_overdue_skips_when_not_due(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_AUTO_SYNC", "true")
    recent = datetime.now(timezone.utc).isoformat()
    with (
        patch("app.designations_scheduler.ensure_scheduler_alive", return_value=True),
        patch(
            "app.designations_scheduler._last_success_at",
            new=AsyncMock(return_value=recent),
        ),
        patch(
            "app.designations_scheduler.start_sync_background", return_value=True
        ) as start,
    ):
        out = await maybe_run_overdue_sync(trigger="watchdog")
    assert out["started"] is False
    assert out["reason"] == "not_due"
    start.assert_not_called()


def test_ensure_scheduler_alive_disabled(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_AUTO_SYNC", "false")
    assert ensure_scheduler_alive() is False
