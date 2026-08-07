from datetime import date

from app.designation_filters import (
    aia_calendar_window_clause,
    current_season_label,
    designations_page_query,
    manual_recent_window_clause,
    parse_season,
    published_referee_designations_season_query,
    season_label_from_iso,
    volatile_sync_prune_clause,
)


def test_season_label():
    assert season_label_from_iso("2025-09-15") == "2025-26"
    assert season_label_from_iso("2026-03-01") == "2025-26"


def test_parse_season():
    start, end = parse_season("2025-26")
    assert start.startswith("2025-08-01")
    assert end.startswith("2026-07-31")


def test_season_august_july_boundaries():
    assert season_label_from_iso("2025-08-01") == "2025-26"
    assert season_label_from_iso("2026-07-31") == "2025-26"
    assert season_label_from_iso("2026-08-01") == "2026-27"


def test_current_season():
    assert current_season_label(date(2026, 5, 21)) == "2025-26"


def test_designations_page_query_structure():
    q = designations_page_query({"batchAt": "2026-05-22T10:00:00+00:00"})
    assert "$and" in q
    assert "$or" in q["$and"][-1]
    branches = q["$and"][-1]["$or"]
    assert any("refereeSection" in str(b) for b in branches)


def test_aia_calendar_window():
    c = aia_calendar_window_clause(ref=date(2026, 5, 21))
    assert "refereeSection" in str(c)
    # matchDate lives inside $and window clause
    blob = str(c)
    assert "2026-05-14" in blob
    assert "$gte" in blob


def test_manual_window():
    c = manual_recent_window_clause(ref=date(2026, 5, 21))
    assert c["source"] == "manual"
    assert "$gte" in c["matchDate"]


def test_volatile_sync_prune_window():
    c = volatile_sync_prune_clause(ref=date(2026, 5, 21))
    assert c["matchDate"]["$gte"].startswith("2026-04-30")
    assert c["matchDate"]["$lte"].startswith("2026-06-11")


def test_season_stats_query_august_to_july():
    q = published_referee_designations_season_query("2025-26")
    assert "$and" in q
    assert q["$and"][0]["status"] == "published"
    assert q["$and"][0]["matchDate"]["$gte"].startswith("2025-08-01")
    assert q["$and"][0]["matchDate"]["$lte"].startswith("2026-07-31")
