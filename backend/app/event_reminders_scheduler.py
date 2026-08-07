"""Scheduler promemoria email eventi."""

from __future__ import annotations

import asyncio
import logging
import os

from .event_reminders import process_event_reminders

logger = logging.getLogger(__name__)

_task: asyncio.Task | None = None
_lock = asyncio.Lock()


def _env_bool(key: str, default: str = "true") -> bool:
    return os.environ.get(key, default).lower() in ("1", "true", "yes", "on")


def _interval_seconds() -> float:
    minutes = float(os.environ.get("EVENT_REMINDERS_INTERVAL_MINUTES", "5"))
    return max(1.0, minutes) * 60.0


def _startup_delay_seconds() -> float:
    return float(os.environ.get("EVENT_REMINDERS_STARTUP_DELAY_SEC", "60"))


async def run_event_reminders(trigger: str = "scheduled") -> dict | None:
    if not _env_bool("EVENT_REMINDERS_ENABLED", "true"):
        return None
    if _lock.locked():
        logger.warning("Event reminders already in progress, skipping (%s)", trigger)
        return None
    async with _lock:
        try:
            result = await process_event_reminders()
            result["trigger"] = trigger
            if result.get("sent") or result.get("errors"):
                logger.info(
                    "Event reminders (%s): sent=%s skipped=%s errors=%s",
                    trigger,
                    result.get("sent"),
                    result.get("skipped"),
                    result.get("errors"),
                )
            return result
        except Exception:
            logger.exception("Event reminders failed (%s)", trigger)
            return None


async def _scheduler_loop() -> None:
    interval = _interval_seconds()
    delay = _startup_delay_seconds()
    logger.info(
        "Event reminders: first run in %.0fs, then every %.1f min", delay, interval / 60
    )
    await asyncio.sleep(delay)
    await run_event_reminders(trigger="startup")
    while True:
        await asyncio.sleep(interval)
        await run_event_reminders(trigger="scheduled")


def start_event_reminders_scheduler() -> None:
    global _task
    if not _env_bool("EVENT_REMINDERS_ENABLED", "true"):
        logger.info("Event reminders disabled (EVENT_REMINDERS_ENABLED=false)")
        return
    if _task is not None and not _task.done():
        return
    _task = asyncio.create_task(_scheduler_loop(), name="event-reminders-scheduler")
    logger.info(
        "Event reminders scheduler started (interval=%s min)",
        os.environ.get("EVENT_REMINDERS_INTERVAL_MINUTES", "5"),
    )


def stop_event_reminders_scheduler() -> None:
    global _task
    if _task is not None:
        _task.cancel()
        _task = None
    logger.info("Event reminders scheduler stopped")
