"""Conteggio partite arbitrate per stagione."""

from app.designation_filters import (
    count_refereed_matches_for_season,
    count_refereed_matches_this_season,
)


def test_counts_unique_matches_not_roles():
    rows = [
        {
            "matchDate": "2026-05-24T12:00:00+00:00",
            "matchHome": "A",
            "matchAway": "B",
            "role": "Arbitro",
            "memberName": "Mario Rossi",
        },
        {
            "matchDate": "2026-05-24T12:00:00+00:00",
            "matchHome": "A",
            "matchAway": "B",
            "role": "Assistente 1",
            "memberName": "Luigi Verdi",
        },
        {
            "matchDate": "2026-05-24T12:00:00+00:00",
            "matchHome": "A",
            "matchAway": "B",
            "role": "Assistente 2",
            "memberName": "Anna Bianchi",
        },
        {
            "matchDate": "2026-05-20T12:00:00+00:00",
            "matchHome": "C",
            "matchAway": "D",
            "role": "Arbitro",
            "memberName": "Paolo Neri",
        },
    ]
    assert count_refereed_matches_for_season(rows, "2025-26") == 2


def test_counts_august_match_in_same_season():
    rows = [
        {
            "matchDate": "2025-09-10T12:00:00+00:00",
            "matchHome": "X",
            "matchAway": "Y",
            "role": "Arbitro",
        },
        {
            "matchDate": "2026-05-24T12:00:00+00:00",
            "matchHome": "A",
            "matchAway": "B",
            "role": "Arbitro",
        },
    ]
    assert count_refereed_matches_for_season(rows, "2025-26") == 2


def test_excludes_observers():
    rows = [
        {
            "matchDate": "2026-05-24T12:00:00+00:00",
            "matchHome": "A",
            "matchAway": "B",
            "role": "Osservatore",
            "memberName": "X",
        },
    ]
    assert count_refereed_matches_this_season(rows) == 0
