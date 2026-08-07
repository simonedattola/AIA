"""Shared admin route dependencies."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from ...paths import UPLOAD_DIR
from ...security import require_admin

logger = logging.getLogger("app.routes.admin")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
