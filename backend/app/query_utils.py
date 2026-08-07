"""Shared helpers for public/admin query params."""
from __future__ import annotations

import re


def clamp_limit(limit: int | None, *, default: int = 20, max_limit: int = 200) -> int:
    try:
        value = int(limit) if limit is not None else default
    except (TypeError, ValueError):
        value = default
    return max(1, min(value, max_limit))


def clamp_skip(skip: int | None) -> int:
    try:
        value = int(skip) if skip is not None else 0
    except (TypeError, ValueError):
        value = 0
    return max(0, value)


def safe_regex(text: str, *, max_len: int = 80) -> str:
    """Escape user input for MongoDB $regex and bound length (ReDoS / injection)."""
    cleaned = (text or "").strip()[:max_len]
    return re.escape(cleaned)
