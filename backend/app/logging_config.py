"""Structured JSON logging for stdout (ELK / Datadog / CloudWatch friendly)."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

from pythonjsonlogger.json import JsonFormatter

_CONFIGURED = False

_RESERVED = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "asctime",
        "taskName",
    }
)


class _AIAJsonFormatter(JsonFormatter):
    """Emit one JSON object per log line with stable field names."""

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        if "event" not in log_record:
            log_record["event"] = record.getMessage()
        log_record.setdefault("service", "aia-legnano-api")
        # Drop redundant defaults that confuse aggregators
        for k in ("levelname", "name", "color_message"):
            log_record.pop(k, None)


def configure_logging(level: str | None = None) -> None:
    """Configure root logging once for JSON stdout (idempotent)."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_level = (level or os.environ.get("LOG_LEVEL") or "INFO").upper()
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(
        _AIAJsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "timestamp"},
        )
    )
    root.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    _CONFIGURED = True


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    """
    Log a structured event.

    Example:
        log_event(logger, "admin_login_attempt", email=email, outcome="success")
    """
    safe = {k: v for k, v in fields.items() if k not in _RESERVED}
    safe["event"] = event
    logger.log(level, event, extra=safe)
