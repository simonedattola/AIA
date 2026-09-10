"""Tests for designations scheduler interval, catch-up, watchdog, stale lock."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

import app.designations_scheduler as sched
from app.designations_scheduler import (
    DEFAULT_INTERVAL_HOURS,
    ensure_scheduler_alive,
    force_release_sync_lock,
    interval_hours,
    is_sync_running,
    is_sync_stale,
    maybe_run_overdue_sync,
    recover_stale_sync_lock,
    run_sync_awaited,
    seconds_until_due,
    start_sync_background,
    sync_runtime_status,
)


@pytest.fixture(autouse=True)
def _reset_scheduler_state():
    """Isolate in-memory lock flags between tests."""
    sched._task = None
    sched._sync_task = None
    sched._lock = asyncio.Lock()
    sched._running = False
    sched._pending = False
    sched._started_at = None
    sched._pending_at = None
    sched._trigger = None
    sched._last_heartbeat_at = None
    sched._last_loop_error = None
    sched._last_stale_recovery = None
    yield
    if sched._sync_task is not None and not sched._sync_task.done():
        sched._sync_task.cancel()
    if sched._task is not None and not sched._task.done():
        sched._task.cancel()
    sched._task = None
    sched._sync_task = None
    sched._running = False
    sched._pending = False
    sched._started_at = None
    sched._pending_at = None
    sched._trigger = None
    sched._lock = asyncio.Lock()


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


def test_stale_lock_detected_when_started_at_old(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_SYNC_STALE_SEC", "600")
    now = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
    sched._running = True
    sched._started_at = (now - timedelta(minutes=20)).isoformat()
    sched._trigger = "health"
    assert is_sync_running() is True
    assert is_sync_stale(now=now) is True


def test_fresh_lock_not_stale(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_SYNC_STALE_SEC", "600")
    now = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
    sched._running = True
    sched._started_at = (now - timedelta(minutes=2)).isoformat()
    assert is_sync_stale(now=now) is False


def test_pending_without_timestamp_is_stale():
    sched._pending = True
    sched._pending_at = None
    sched._started_at = None
    assert is_sync_stale() is True


def test_recover_stale_sync_lock_clears_flags(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_SYNC_STALE_SEC", "60")
    now = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
    sched._pending = True
    sched._running = True
    sched._started_at = (now - timedelta(minutes=30)).isoformat()
    sched._pending_at = sched._started_at
    sched._trigger = "health"
    out = recover_stale_sync_lock(now=now)
    assert out["recovered"] is True
    assert is_sync_running() is False
    assert sched._started_at is None
    assert sync_runtime_status()["lastStaleRecovery"]["reason"] == "stale_timeout"


def test_recover_fresh_lock_does_not_clear(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_SYNC_STALE_SEC", "600")
    now = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
    sched._running = True
    sched._started_at = (now - timedelta(seconds=30)).isoformat()
    out = recover_stale_sync_lock(now=now)
    assert out["recovered"] is False
    assert out["reason"] == "fresh"
    assert is_sync_running() is True


def test_force_release_replaces_locked_asyncio_lock():
    # Simulate a stuck lock held without an owner coroutine we can exit.
    lock = asyncio.Lock()
    lock._locked = True  # type: ignore[attr-defined]
    sched._lock = lock
    assert sched._lock.locked()
    sched._running = True
    sched._started_at = "2026-09-08T19:00:00+00:00"
    force_release_sync_lock(reason="test")
    assert sched._lock.locked() is False
    assert is_sync_running() is False
    assert sched._lock is not lock


@pytest.mark.asyncio
async def test_start_sync_background_force_when_stuck(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_SYNC_STALE_SEC", "600")
    sched._pending = True
    sched._pending_at = datetime.now(timezone.utc).isoformat()
    assert start_sync_background("manual") is False
    assert start_sync_background("manual", force=True) is True
    assert sched._pending is True
    assert sched._sync_task is not None
    sched._sync_task.cancel()
    try:
        await sched._sync_task
    except (asyncio.CancelledError, Exception):
        pass


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
        out = await maybe_run_overdue_sync(trigger="watchdog", await_completion=False)
    assert out["started"] is True
    assert out["reason"] == "overdue"
    start.assert_called_once_with("watchdog", force=False)


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
        out = await maybe_run_overdue_sync(trigger="watchdog", await_completion=False)
    assert out["started"] is False
    assert out["reason"] == "not_due"
    start.assert_not_called()


@pytest.mark.asyncio
async def test_maybe_run_overdue_awaits_completion(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_AUTO_SYNC", "true")
    fake = {"ok": True, "inserted": 3, "pagesFetched": 2, "errors": []}
    with (
        patch("app.designations_scheduler.ensure_scheduler_alive", return_value=True),
        patch(
            "app.designations_scheduler._last_success_at",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.designations_scheduler.run_auto_sync",
            new=AsyncMock(return_value=fake),
        ) as run,
    ):
        out = await maybe_run_overdue_sync(trigger="cron", await_completion=True)
    assert out["started"] is True
    assert out["completed"] is True
    assert out["reason"] == "overdue_awaited"
    run.assert_awaited_once()


@pytest.mark.asyncio
async def test_maybe_run_overdue_recovers_stale_then_awaits(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_AUTO_SYNC", "true")
    monkeypatch.setenv("DESIGNATIONS_SYNC_STALE_SEC", "60")
    now = datetime.now(timezone.utc)
    sched._running = True
    sched._started_at = (now - timedelta(minutes=30)).isoformat()
    fake = {"ok": True, "inserted": 1, "pagesFetched": 1, "errors": []}
    with (
        patch("app.designations_scheduler.ensure_scheduler_alive", return_value=True),
        patch(
            "app.designations_scheduler._last_success_at",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.designations_scheduler.run_auto_sync",
            new=AsyncMock(return_value=fake),
        ),
    ):
        out = await maybe_run_overdue_sync(trigger="health", await_completion=True)
    assert out["started"] is True
    assert out["completed"] is True
    assert (out.get("staleRecovery") or {}).get("recovered") is True


@pytest.mark.asyncio
async def test_run_sync_awaited_force_overrides_fresh_lock(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_SYNC_STALE_SEC", "3600")
    sched._running = True
    sched._started_at = datetime.now(timezone.utc).isoformat()
    fake = {"ok": True, "inserted": 0, "pagesFetched": 0, "errors": []}
    with patch(
        "app.designations_scheduler.run_auto_sync",
        new=AsyncMock(return_value=fake),
    ):
        blocked = await run_sync_awaited(trigger="manual", force=False)
        assert blocked["reason"] == "already_running"
        forced = await run_sync_awaited(trigger="manual", force=True)
    assert forced["started"] is True
    assert forced["completed"] is True


@pytest.mark.asyncio
async def test_health_default_awaits_when_env_default(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_AUTO_SYNC", "true")
    monkeypatch.delenv("DESIGNATIONS_SYNC_AWAIT_ON_HEALTH", raising=False)
    fake = {"ok": True, "inserted": 1, "pagesFetched": 1, "errors": []}
    with (
        patch("app.designations_scheduler.ensure_scheduler_alive", return_value=True),
        patch(
            "app.designations_scheduler._last_success_at",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.designations_scheduler.run_auto_sync",
            new=AsyncMock(return_value=fake),
        ) as run,
        patch(
            "app.designations_scheduler.start_sync_background", return_value=True
        ) as start,
    ):
        out = await maybe_run_overdue_sync(trigger="health")
    assert out["reason"] == "overdue_awaited"
    run.assert_awaited_once()
    start.assert_not_called()


def test_ensure_scheduler_alive_disabled(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_AUTO_SYNC", "false")
    assert ensure_scheduler_alive() is False


@pytest.mark.asyncio
async def test_overdue_respects_retry_backoff_after_empty(monkeypatch):
    monkeypatch.setenv("DESIGNATIONS_AUTO_SYNC", "true")
    monkeypatch.setenv("DESIGNATIONS_SYNC_RETRY_BACKOFF_SEC", "900")
    monkeypatch.setattr(
        "app.designations_scheduler.ensure_scheduler_alive", lambda: True
    )
    monkeypatch.setattr(
        "app.designations_scheduler._last_success_at",
        AsyncMock(return_value="2020-01-01T00:00:00+00:00"),
    )
    monkeypatch.setattr(
        "app.designations_scheduler._last_attempt_doc",
        AsyncMock(
            return_value={
                "at": datetime.now(timezone.utc).isoformat(),
                "status": "empty",
                "error": "cloudflare",
            }
        ),
    )
    out = await maybe_run_overdue_sync(trigger="health", await_completion=True)
    assert out["reason"] == "retry_backoff"
    assert out["started"] is False
