from datetime import date

from app.designation_queries import upcoming_match_date_clause


def test_upcoming_match_date_clause_uses_iso_day_prefix():
    clause = upcoming_match_date_clause(date(2026, 6, 6))
    assert clause == {"matchDate": {"$gte": "2026-06-06"}}
