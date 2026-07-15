"""Sync non deve cancellare lo storico designazioni."""
from app.designation_filters import designations_page_query, published_referee_designations_season_query
from app.designations_sync import _national_hub_slugs


def test_national_hubs_default_includes_configured_hubs():
    hubs = _national_hub_slugs()
    for slug in ("canc", "cand", "can5elite", "can5", "canbs"):
        assert slug in hubs


def test_page_query_uses_date_window_not_batch():
    q = designations_page_query({"batchAt": "2020-01-01T00:00:00+00:00"})
    s = str(q)
    assert "syncBatchAt" not in s
    assert "matchDate" in s


def test_season_stats_filters_legnano_section():
    q = published_referee_designations_season_query("2025-26", "Legnano")
    assert "refereeSection" in str(q)
