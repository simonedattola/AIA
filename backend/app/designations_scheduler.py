"""Background scheduler: sync Legnano designations from AIA FIGC every N hours."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone

from .designations_sync import sync_from_aia_lombardia

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_HOURS = 6.0

_task: asyncio.Task | None = None
_lock = asyncio.Lock()
_running = False
_pending = False
_started_at: str | None = None
_trigger: str | None = None


def _env_bool(key: str, default: str = "true") -> bool:
    return os.environ.get(key, default).lower() in ("1", "true", "yes", "on")


def interval_hours() -> float:
    raw = os.environ.get(
        "DESIGNATIONS_SYNC_INTERVAL_HOURS", str(DEFAULT_INTERVAL_HOURS)
    )
    try:
        hours = float(raw)
    except (TypeError, ValueError):
        hours = DEFAULT_INTERVAL_HOURS
    return max(1.0, hours)


def _interval_seconds() -> float:
    return interval_hours() * 3600.0


def _startup_delay_seconds() -> float:
    return float(os.environ.get("DESIGNATIONS_SYNC_STARTUP_DELAY_SEC", "90"))


def _parse_iso(value: str | None) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def seconds_until_due(
    last_success_at: str | None,
    *,
    now: datetime | None = None,
    interval_sec: float | None = None,
) -> float:
    """Seconds to wait before next sync. 0 = overdue / never ran."""
    interval = interval_sec if interval_sec is not None else _interval_seconds()
    last = _parse_iso(last_success_at)
    if last is None:
        return 0.0
    current = now or datetime.now(timezone.utc)
    elapsed = (current - last).total_seconds()
    return max(0.0, interval - elapsed)


def is_sync_running() -> bool:
    return _pending or _running or _lock.locked()


def sync_runtime_status() -> dict:
    return {
        "running": is_sync_running(),
        "startedAt": _started_at,
        "trigger": _trigger,
        "intervalHours": interval_hours(),
    }


async def _mark_attempt(trigger: str, *, status: str, error: str | None = None) -> None:
    from .db import get_db
    from .designations_sync import _now

    db = get_db()
    doc = {
        "at": _now(),
        "trigger": trigger,
        "status": status,
    }
    if error:
        doc["error"] = error[:500]
    await db.site_settings.update_one(
        {"id": "site-settings"},
        {"$set": {"lastDesignationsSyncAttempt": doc}},
        upsert=True,
    )


async def _last_success_at() -> str | None:
    from .db import get_db

    db = get_db()
    settings = await db.site_settings.find_one(
        {"id": "site-settings"},
        {"_id": 0, "lastDesignationsSync.at": 1},
    )
    if not settings:
        return None
    last = settings.get("lastDesignationsSync") or {}
    return last.get("at")


async def run_auto_sync(trigger: str = "scheduled") -> dict | None:
    """Run one sync cycle (Legnano section, Legnano referees only)."""
    global _running, _started_at, _trigger
    if not _env_bool("DESIGNATIONS_AUTO_SYNC", "true") and trigger != "manual":
        return None

    if _lock.locked():
        logger.warning("Designations sync already in progress, skipping (%s)", trigger)
        return None

    async with _lock:
        from .designations_sync import _now

        _running = True
        _trigger = trigger
        _started_at = _now()
        try:
            logger.info("Designations auto-sync started (%s)", trigger)
            await _mark_attempt(trigger, status="running")
            result = await sync_from_aia_lombardia(
                section_gare=os.environ.get("DESIGNATIONS_LEGNANO_GARE", "3-270"),
                filter_section=os.environ.get("DESIGNATIONS_FILTER_SECTION", "Legnano"),
                replace_existing=True,
                trigger=trigger,
            )
            result["trigger"] = trigger
            result["intervalHours"] = interval_hours()
            logger.info(
                "Designations auto-sync done (%s): %d inserted, %d pages, %d errors",
                trigger,
                result.get("inserted", 0),
                result.get("pagesFetched", 0),
                len(result.get("errors") or []),
            )
            await _mark_attempt(trigger, status="success")
            return result
        except Exception as exc:
            logger.exception("Designations auto-sync failed (%s)", trigger)
            await _mark_attempt(trigger, status="failed", error=str(exc))
            return None
        finally:
            _running = False
            _started_at = None
            _trigger = None


def start_sync_background(trigger: str = "manual") -> bool:
    """Kick off sync without blocking HTTP. False if already running."""
    global _pending, _trigger
    if is_sync_running():
        return False
    _pending = True
    _trigger = trigger

    async def _run() -> None:
        global _pending
        try:
            await run_auto_sync(trigger=trigger)
        finally:
            _pending = False

    asyncio.create_task(_run(), name=f"designations-sync-{trigger}")
    return True


async def _scheduler_loop() -> None:
    interval = _interval_seconds()
    delay = _startup_delay_seconds()
    logger.info(
        "Designations auto-sync: first check in %.0fs, then every %.1f h (catch-up if overdue)",
        delay,
        interval / 3600,
    )
    await asyncio.sleep(delay)

    while True:
        last_at = await _last_success_at()
        wait = seconds_until_due(last_at, interval_sec=interval)
        if wait > 0:
            logger.info(
                "Designations sync next in %.0fs (last success=%s)",
                wait,
                last_at or "never",
            )
            await asyncio.sleep(min(wait, 300.0))
            continue
        trigger = "startup" if last_at is None else "scheduled"
        await run_auto_sync(trigger=trigger)
        await asyncio.sleep(30.0)


def start_designations_scheduler() -> None:
    """Start background task (idempotent)."""
    global _task
    if not _env_bool("DESIGNATIONS_AUTO_SYNC", "true"):
        logger.info("Designations auto-sync disabled (DESIGNATIONS_AUTO_SYNC=false)")
        return
    if _task is not None and not _task.done():
        return
    _task = asyncio.create_task(_scheduler_loop(), name="designations-sync-scheduler")
    logger.info(
        "Designations scheduler started (interval=%s h, section=%s, filter=%s)",
        interval_hours(),
        os.environ.get("DESIGNATIONS_LEGNANO_GARE", "3-270"),
        os.environ.get("DESIGNATIONS_FILTER_SECTION", "Legnano"),
    )


def stop_designations_scheduler() -> None:
    global _task
    if _task is not None:
        _task.cancel()
        _task = None
    logger.info("Designations scheduler stopped")
