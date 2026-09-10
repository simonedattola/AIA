"""Background scheduler: sync Legnano designations from AIA FIGC every N hours.

Reliability notes (Railway Free Serverless):
- The asyncio loop must never die on a transient Mongo/network error.
- Railway restarts wipe in-memory timers; catch-up uses last success in Mongo.
- Fire-and-forget ``asyncio.create_task`` after an HTTP response is unsafe:
  Serverless freezes/sleeps the process and the sync never finishes, while
  in-memory ``_pending``/``_running``/``_lock`` can stick and block retries.
- Prefer ``await_completion=True`` on health/cron so the request keeps the
  process awake until sync completes. Stale locks are force-released.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone

from .designations_sync import sync_from_aia_lombardia

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_HOURS = 6.0
DEFAULT_STALE_SYNC_SEC = 720.0  # 12 minutes

_task: asyncio.Task | None = None
_sync_task: asyncio.Task | None = None
_lock = asyncio.Lock()
_running = False
_pending = False
_started_at: str | None = None
_pending_at: str | None = None
_trigger: str | None = None
_last_heartbeat_at: str | None = None
_last_loop_error: str | None = None
_last_stale_recovery: dict | None = None


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


def stale_sync_seconds() -> float:
    raw = os.environ.get("DESIGNATIONS_SYNC_STALE_SEC", str(DEFAULT_STALE_SYNC_SEC))
    try:
        sec = float(raw)
    except (TypeError, ValueError):
        sec = DEFAULT_STALE_SYNC_SEC
    return max(60.0, sec)


def await_on_health() -> bool:
    """Keep HTTP request open until sync finishes (Serverless-safe)."""
    return _env_bool("DESIGNATIONS_SYNC_AWAIT_ON_HEALTH", "true")


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


def is_scheduler_alive() -> bool:
    return _task is not None and not _task.done()


def sync_age_seconds(*, now: datetime | None = None) -> float | None:
    """Age of current run from startedAt or pendingAt; None if not running."""
    if not is_sync_running():
        return None
    current = now or datetime.now(timezone.utc)
    marker = _parse_iso(_started_at) or _parse_iso(_pending_at)
    if marker is None:
        return None
    return max(0.0, (current - marker).total_seconds())


def is_sync_stale(*, now: datetime | None = None) -> bool:
    """True when a run flag is stuck longer than the stale threshold."""
    if not is_sync_running():
        return False
    age = sync_age_seconds(now=now)
    if age is None:
        # Flags set without timestamps (corrupt / interrupted) → treat as stale.
        return True
    return age >= stale_sync_seconds()


def sync_runtime_status() -> dict:
    age = sync_age_seconds()
    return {
        "running": is_sync_running(),
        "startedAt": _started_at,
        "pendingAt": _pending_at,
        "trigger": _trigger,
        "intervalHours": interval_hours(),
        "schedulerAlive": is_scheduler_alive(),
        "autoSyncEnabled": _env_bool("DESIGNATIONS_AUTO_SYNC", "true"),
        "lastHeartbeatAt": _last_heartbeat_at,
        "lastLoopError": _last_loop_error,
        "staleAfterSec": stale_sync_seconds(),
        "runningAgeSec": age,
        "stale": is_sync_stale(),
        "lastStaleRecovery": _last_stale_recovery,
        "awaitOnHealth": await_on_health(),
    }


def force_release_sync_lock(*, reason: str = "stale") -> dict:
    """
    Clear in-memory running flags / replace a stuck asyncio.Lock.
    Safe to call when a previous Serverless freeze left flags true forever.
    """
    global _lock, _running, _pending, _started_at, _pending_at, _trigger
    global _sync_task, _last_stale_recovery
    from .designations_sync import _now

    was_running = is_sync_running()
    age = sync_age_seconds()
    cancelled = False
    if _sync_task is not None and not _sync_task.done():
        _sync_task.cancel()
        cancelled = True
    _sync_task = None
    _running = False
    _pending = False
    _started_at = None
    _pending_at = None
    _trigger = None
    if _lock.locked():
        _lock = asyncio.Lock()
    _last_stale_recovery = {
        "at": _now(),
        "reason": reason,
        "ageSec": age,
        "cancelledTask": cancelled,
    }
    if was_running:
        logger.warning(
            "Designations sync lock force-released (%s, ageSec=%s, cancelled=%s)",
            reason,
            age,
            cancelled,
        )
    return {"recovered": was_running, **(_last_stale_recovery or {})}


def recover_stale_sync_lock(*, now: datetime | None = None) -> dict:
    """Release the in-memory lock only when the current run looks stale."""
    if not is_sync_running():
        return {"recovered": False, "reason": "not_running"}
    if not is_sync_stale(now=now):
        age = sync_age_seconds(now=now)
        return {
            "recovered": False,
            "reason": "fresh",
            "ageSec": age,
            "staleAfterSec": stale_sync_seconds(),
        }
    return force_release_sync_lock(reason="stale_timeout")


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


async def _write_heartbeat(*, note: str = "") -> None:
    global _last_heartbeat_at
    from .db import get_db
    from .designations_sync import _now

    _last_heartbeat_at = _now()
    db = get_db()
    doc = {
        "at": _last_heartbeat_at,
        "schedulerAlive": True,
        "intervalHours": interval_hours(),
        "note": note,
    }
    await db.site_settings.update_one(
        {"id": "site-settings"},
        {"$set": {"designationsSchedulerHeartbeat": doc}},
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


async def _last_attempt_doc() -> dict | None:
    from .db import get_db

    db = get_db()
    settings = await db.site_settings.find_one(
        {"id": "site-settings"},
        {"_id": 0, "lastDesignationsSyncAttempt": 1},
    )
    if not settings:
        return None
    doc = settings.get("lastDesignationsSyncAttempt") or {}
    return doc or None


def _retry_backoff_seconds() -> float:
    raw = os.environ.get("DESIGNATIONS_SYNC_RETRY_BACKOFF_SEC", "900")
    try:
        return max(60.0, float(raw))
    except (TypeError, ValueError):
        return 900.0


async def run_auto_sync(trigger: str = "scheduled") -> dict | None:
    """Run one sync cycle (Legnano section, Legnano referees only)."""
    global _running, _started_at, _pending_at, _trigger, _pending
    if not _env_bool("DESIGNATIONS_AUTO_SYNC", "true") and trigger != "manual":
        logger.warning(
            "Skipping auto-sync (%s): DESIGNATIONS_AUTO_SYNC is disabled", trigger
        )
        return None

    if _lock.locked():
        logger.warning("Designations sync already in progress, skipping (%s)", trigger)
        return None

    async with _lock:
        from .designations_sync import _now

        _running = True
        _pending = False
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
            # Empty scrape returns ok=False and does not bump lastDesignationsSync.
            if result.get("ok") is False:
                await _mark_attempt(
                    trigger,
                    status="empty",
                    error=str(result.get("error") or "empty scrape")[:500],
                )
            else:
                await _mark_attempt(trigger, status="success")
            return result
        except Exception as exc:
            logger.exception("Designations auto-sync failed (%s)", trigger)
            await _mark_attempt(trigger, status="failed", error=str(exc))
            return None
        finally:
            _running = False
            _started_at = None
            _pending_at = None
            _trigger = None


def start_sync_background(trigger: str = "manual", *, force: bool = False) -> bool:
    """Kick off sync without blocking HTTP. False if already running (unless force)."""
    global _pending, _pending_at, _trigger, _sync_task
    from .designations_sync import _now

    if force and is_sync_running():
        force_release_sync_lock(reason="force_start")
    elif is_sync_running():
        recover = recover_stale_sync_lock()
        if not recover.get("recovered") and is_sync_running():
            return False

    _pending = True
    _pending_at = _now()
    _trigger = trigger

    async def _run() -> None:
        global _pending, _pending_at, _sync_task
        try:
            await run_auto_sync(trigger=trigger)
        finally:
            _pending = False
            _pending_at = None
            if _sync_task is asyncio.current_task():
                _sync_task = None

    _sync_task = asyncio.create_task(_run(), name=f"designations-sync-{trigger}")
    return True


async def run_sync_awaited(trigger: str = "cron", *, force: bool = False) -> dict:
    """
    Run sync in the current request (keeps Serverless process awake).
    Recovers a stale lock; refuses a fresh concurrent run unless force=True.
    """
    recovery = None
    if force and is_sync_running():
        recovery = force_release_sync_lock(reason="force_await")
    elif is_sync_running():
        recovery = recover_stale_sync_lock()
        if is_sync_running():
            return {
                "started": False,
                "completed": False,
                "reason": "already_running",
                "staleRecovery": recovery,
                **sync_runtime_status(),
            }

    result = await run_auto_sync(trigger=trigger)
    ok = bool(result) and result.get("ok") is not False
    return {
        "started": True,
        "completed": True,
        "reason": "completed" if ok else "completed_with_errors",
        "result": result,
        "staleRecovery": recovery,
        **sync_runtime_status(),
    }


async def maybe_run_overdue_sync(
    trigger: str = "watchdog",
    *,
    await_completion: bool | None = None,
    force: bool = False,
) -> dict:
    """
    If last success is overdue, start sync.

    ``await_completion=True`` runs sync inline (Serverless-safe).
    Default for trigger ``health`` follows ``DESIGNATIONS_SYNC_AWAIT_ON_HEALTH``.
    """
    ensure_scheduler_alive()
    if await_completion is None:
        await_completion = trigger == "health" and await_on_health()

    stale = recover_stale_sync_lock()
    if not _env_bool("DESIGNATIONS_AUTO_SYNC", "true") and trigger != "manual":
        return {
            "started": False,
            "reason": "auto_sync_disabled",
            "staleRecovery": stale,
            **sync_runtime_status(),
        }
    if is_sync_running() and not force:
        return {
            "started": False,
            "reason": "already_running",
            "staleRecovery": stale,
            **sync_runtime_status(),
        }
    try:
        last_at = await _last_success_at()
        wait = seconds_until_due(last_at)
    except Exception as exc:
        logger.exception("Overdue check failed")
        return {
            "started": False,
            "reason": "check_failed",
            "error": str(exc)[:200],
            "staleRecovery": stale,
            **sync_runtime_status(),
        }
    if wait > 0 and not force:
        return {
            "started": False,
            "reason": "not_due",
            "secondsUntilNext": wait,
            "lastSuccessAt": last_at,
            "staleRecovery": stale,
            **sync_runtime_status(),
        }

    # Back off after a recent failed/empty attempt (e.g. Cloudflare block) so
    # health checks do not re-crawl for minutes on every probe.
    if not force:
        try:
            attempt = await _last_attempt_doc()
        except Exception:
            attempt = None
        if attempt and attempt.get("status") in ("failed", "empty"):
            attempt_at = _parse_iso(attempt.get("at"))
            if attempt_at is not None:
                age = (datetime.now(timezone.utc) - attempt_at).total_seconds()
                backoff = _retry_backoff_seconds()
                if age < backoff:
                    return {
                        "started": False,
                        "reason": "retry_backoff",
                        "secondsUntilRetry": backoff - age,
                        "lastSuccessAt": last_at,
                        "lastAttempt": attempt,
                        "staleRecovery": stale,
                        **sync_runtime_status(),
                    }

    if await_completion:
        out = await run_sync_awaited(trigger=trigger, force=force)
        try:
            out["lastSuccessAt"] = await _last_success_at()
        except Exception:
            out["lastSuccessAt"] = last_at
        out["staleRecovery"] = stale or out.get("staleRecovery")
        if out.get("started"):
            out["reason"] = "overdue_awaited" if not force else "forced_awaited"
        logger.info(
            "Overdue designations sync awaited (trigger=%s, reason=%s, lastSuccess=%s)",
            trigger,
            out.get("reason"),
            out.get("lastSuccessAt") or "never",
        )
        return out

    started = start_sync_background(trigger, force=force)
    logger.info(
        "Overdue designations sync %s (trigger=%s, lastSuccess=%s)",
        "started" if started else "skipped",
        trigger,
        last_at or "never",
    )
    return {
        "started": started,
        "reason": ("overdue" if started else "start_failed"),
        "lastSuccessAt": last_at,
        "staleRecovery": stale,
        **sync_runtime_status(),
    }


async def _scheduler_loop() -> None:
    global _last_loop_error
    interval = _interval_seconds()
    delay = _startup_delay_seconds()
    logger.info(
        "Designations auto-sync: first check in %.0fs, then every %.1f h "
        "(catch-up if overdue; loop errors are recovered)",
        delay,
        interval / 3600,
    )
    await asyncio.sleep(delay)

    # Heartbeat Mongo only around syncs (not every minute): on Railway Free
    # Serverless, frequent outbound DB traffic prevents sleep and burns the $1 credit.
    heartbeat_every = float(
        os.environ.get("DESIGNATIONS_HEARTBEAT_INTERVAL_SEC", "1800")
    )
    last_hb_mono = 0.0

    while True:
        try:
            recover_stale_sync_lock()
            loop = asyncio.get_running_loop()
            now_mono = loop.time()
            if now_mono - last_hb_mono >= max(300.0, heartbeat_every):
                await _write_heartbeat(note="loop")
                last_hb_mono = now_mono
            _last_loop_error = None
            last_at = await _last_success_at()
            wait = seconds_until_due(last_at, interval_sec=interval)
            if wait > 0:
                logger.info(
                    "Designations sync next in %.0fs (last success=%s)",
                    wait,
                    last_at or "never",
                )
                # Chunked sleep without Mongo chatter (sleep-friendly for Serverless).
                await asyncio.sleep(min(wait, 300.0))
                continue
            trigger = "startup" if last_at is None else "scheduled"
            await _write_heartbeat(note="sync")
            last_hb_mono = asyncio.get_running_loop().time()
            # Await inline inside the long-lived loop task (keeps process busy).
            await run_auto_sync(trigger=trigger)
            await asyncio.sleep(30.0)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            _last_loop_error = str(exc)[:500]
            logger.exception(
                "Designations scheduler loop error; retrying in 60s: %s", exc
            )
            try:
                await asyncio.sleep(60.0)
            except asyncio.CancelledError:
                raise


def ensure_scheduler_alive() -> bool:
    """Restart the loop task if it crashed. Returns True if a task is running."""
    global _task
    if not _env_bool("DESIGNATIONS_AUTO_SYNC", "true"):
        return False
    if _task is not None and not _task.done():
        return True
    if _task is not None and _task.done():
        exc = _task.exception() if not _task.cancelled() else None
        logger.error(
            "Designations scheduler task was dead (exc=%s); restarting",
            exc,
        )
    _task = asyncio.create_task(_scheduler_loop(), name="designations-sync-scheduler")
    logger.info(
        "Designations scheduler started (interval=%s h, section=%s, filter=%s)",
        interval_hours(),
        os.environ.get("DESIGNATIONS_LEGNANO_GARE", "3-270"),
        os.environ.get("DESIGNATIONS_FILTER_SECTION", "Legnano"),
    )
    return True


def start_designations_scheduler() -> None:
    """Start background task (idempotent)."""
    if not _env_bool("DESIGNATIONS_AUTO_SYNC", "true"):
        logger.info("Designations auto-sync disabled (DESIGNATIONS_AUTO_SYNC=false)")
        return
    ensure_scheduler_alive()


def stop_designations_scheduler() -> None:
    global _task, _sync_task
    if _sync_task is not None:
        _sync_task.cancel()
        _sync_task = None
    if _task is not None:
        _task.cancel()
        _task = None
    force_release_sync_lock(reason="scheduler_stop")
    logger.info("Designations scheduler stopped")
