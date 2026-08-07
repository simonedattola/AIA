"""Unit tests for query helpers and rate limiting."""
from app.query_utils import clamp_limit, clamp_skip, safe_regex
from app.rate_limit import enforce_rate_limit, _hits
from fastapi import HTTPException
import pytest


def test_clamp_limit_bounds():
    assert clamp_limit(None, default=20, max_limit=100) == 20
    assert clamp_limit(0, default=20, max_limit=100) == 1
    assert clamp_limit(999, default=20, max_limit=100) == 100
    assert clamp_limit(-5, default=20, max_limit=100) == 1


def test_clamp_skip():
    assert clamp_skip(None) == 0
    assert clamp_skip(-3) == 0
    assert clamp_skip(10) == 10


def test_safe_regex_escapes_specials():
    assert safe_regex("Rossi.*") == r"Rossi\.\*"
    assert safe_regex("  a  ") == "a"
    assert len(safe_regex("x" * 200)) == 80


def test_rate_limit_blocks_after_max():
    _hits.clear()
    key = "test-unit-rate"
    for _ in range(3):
        enforce_rate_limit(key, max_hits=3, window_seconds=60)
    with pytest.raises(HTTPException) as exc:
        enforce_rate_limit(key, max_hits=3, window_seconds=60)
    assert exc.value.status_code == 429
