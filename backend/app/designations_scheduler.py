"""Background scheduler: sync Legnano designations from AIA FIGC every N hours."""
from __future__ import annotations

import asyncio
import logging
import os

from .designations_sync import sync_from_aia_lombardia

logger = logging.getLogger(__name__)

_task: asyncio.Task | None = None
_lock = asyncio.Lock()
_running = False


def _env_bool(key: str, default: str = "true") -> bool:
    return os.environ.get(key, default).lower() in ("1", "true", "yes", "on")


def _interval_seconds() -> float:
    hours = float(os.environ.get("DESIGNATIONS_SYNC_INTERVAL_HOURS", "12"))
    return max(1.0, hours) * 3600.0


def _startup_delay_seconds() -> float:
    return float(os.environ.get("DESIGNATIONS_SYNC_STARTUP_DELAY_SEC", "90"))


async def run_auto_sync(trigger: str = "scheduled") -> dict | None:
    """Run one sync cycle (Legnano section, Legnano referees only)."""
    global _running
    if not _env_bool("DESIGNATIONS_AUTO_SYNC", "true"):
        return None

    if _lock.locked():
        logger.warning("Designations sync already in progress, skipping (%s)", trigger)
        return None

    async with _lock:
        _running = True
        try:
            logger.info("Designations auto-sync started (%s)", trigger)
            result = await sync_from_aia_lombardia(
                section_gare=os.environ.get("DESIGNATIONS_LEGNANO_GARE", "3-270"),
                filter_section=os.environ.get("DESIGNATIONS_FILTER_SECTION", "Legnano"),
                replace_existing=True,
            )
            result["trigger"] = trigger
            logger.info(
                "Designations auto-sync done (%s): %d inserted, %d pages, %d errors",
                trigger,
                result.get("inserted", 0),
                result.get("pagesFetched", 0),
                len(result.get("errors") or []),
            )
            return result
        except Exception:
            logger.exception("Designations auto-sync failed (%s)", trigger)
            return None
        finally:
            _running = False


async def _scheduler_loop() -> None:
    interval = _interval_seconds()
    run_on_startup = _env_bool("DESIGNATIONS_SYNC_ON_STARTUP", "true")

    if run_on_startup:
        delay = _startup_delay_seconds()
        logger.info(
            "Designations auto-sync: first run in %.0fs, then every %.1f h",
            delay,
            interval / 3600,
        )
        await asyncio.sleep(delay)
        await run_auto_sync(trigger="startup")

    while True:
        await asyncio.sleep(interval)
        await run_auto_sync(trigger="scheduled")


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
        os.environ.get("DESIGNATIONS_SYNC_INTERVAL_HOURS", "12"),
        os.environ.get("DESIGNATIONS_LEGNANO_GARE", "3-270"),
        os.environ.get("DESIGNATIONS_FILTER_SECTION", "Legnano"),
    )


def stop_designations_scheduler() -> None:
    global _task
    if _task is not None:
        _task.cancel()
        _task = None
    logger.info("Designations scheduler stopped")
