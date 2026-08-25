"""Test purge designazioni per stagione."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.designation_filters import match_date_in_season_clause, parse_season
from app.seed import ensure_purge_designations_2022_23


def test_parse_season_2022_23():
    bounds = parse_season("2022-23")
    assert bounds is not None
    start, end = bounds
    assert start.startswith("2022-08-01")
    assert end.startswith("2023-07-31")
    clause = match_date_in_season_clause("2022-23")
    assert clause["matchDate"]["$gte"].startswith("2022-08-01")
    assert clause["matchDate"]["$lte"].startswith("2023-07-31")


@pytest.mark.asyncio
async def test_ensure_purge_designations_2022_23_deletes_once():
    db = MagicMock()
    db.designations.count_documents = AsyncMock(return_value=3)
    db.designations.delete_many = AsyncMock(return_value=MagicMock(deleted_count=3))

    with patch("app.seed._seed_flag", new=AsyncMock(return_value=False)):
        with patch("app.seed._set_seed_flag", new=AsyncMock()) as set_flag:
            with patch("app.seed.get_db", return_value=db):
                n = await ensure_purge_designations_2022_23()
    assert n == 3
    db.designations.delete_many.assert_awaited_once()
    set_flag.assert_awaited_once_with("purge_designations_2022_23")

    with patch("app.seed._seed_flag", new=AsyncMock(return_value=True)):
        with patch("app.seed.get_db", return_value=db):
            n2 = await ensure_purge_designations_2022_23()
    assert n2 == 0
