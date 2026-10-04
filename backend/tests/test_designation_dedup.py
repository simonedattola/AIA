"""Dedup designazioni: stessa gara su hub diversi e date ±2 giorni."""

from datetime import date

from app.designations_sync import (
    _dedupe_scraped_rows,
    _designation_identity_key,
    _designation_match_key,
    _parse_match_day,
    _pick_near_date_keepers,
    _source_priority,
)
from app.scrapers.aia_lombardia import ScrapedDesignation, _external_id


class TestExternalId:
    def test_same_match_different_gare_same_id(self):
        a = _external_id(
            "2026-05-24", "Milan SPA", "Arezzo", "Arbitro", "Gabriele Re Calegari"
        )
        b = _external_id(
            "2026-05-24", "Milan SPA", "Arezzo", "Arbitro", "Gabriele Re Calegari"
        )
        assert a == b

    def test_different_date_different_id(self):
        a = _external_id("2026-05-24", "A", "B", "Arbitro", "Mario Rossi")
        b = _external_id("2026-05-25", "A", "B", "Arbitro", "Mario Rossi")
        assert a != b


class TestDedupeScrapedRows:
    def test_prefers_lombardia_source(self):
        row_lomb = ScrapedDesignation(
            external_id="abc",
            match_date="2026-05-24",
            championship="X",
            match_home="A",
            match_away="B",
            match_label="A - B",
            role="Arbitro",
            member_name="Mario Rossi",
            source="aia-figc-lombardia",
        )
        row_tos = ScrapedDesignation(
            external_id="abc",
            match_date="2026-05-24",
            championship="Y",
            match_home="A",
            match_away="B",
            match_label="A - B",
            role="Arbitro",
            member_name="Mario Rossi",
            source="aia-figc-toscana",
        )
        out = _dedupe_scraped_rows([row_tos, row_lomb])
        assert len(out) == 1
        assert out[0].source == "aia-figc-lombardia"

    def test_keeps_earliest_date_within_two_days(self):
        early = ScrapedDesignation(
            external_id="e1",
            match_date="2026-10-03",
            championship="Serie C",
            match_home="Como 1907 SRL",
            match_away="Roma SRL",
            match_label="Como 1907 SRL - Roma SRL",
            role="Arbitro",
            member_name="Alessandro Raffuzzi",
            source="aia-figc-canc",
        )
        late = ScrapedDesignation(
            external_id="e2",
            match_date="2026-10-04",
            championship="Serie C",
            match_home="Como 1907 SRL",
            match_away="Roma SRL",
            match_label="Como 1907 SRL - Roma SRL",
            role="Arbitro",
            member_name="Alessandro Raffuzzi",
            source="aia-figc-lombardia",
        )
        out = _dedupe_scraped_rows([late, early])
        assert len(out) == 1
        assert out[0].match_date == "2026-10-03"

    def test_keeps_matches_more_than_two_days_apart(self):
        a = ScrapedDesignation(
            external_id="a",
            match_date="2026-10-03",
            championship="X",
            match_home="A",
            match_away="B",
            match_label="A - B",
            role="Arbitro",
            member_name="Mario Rossi",
            source="aia-figc-lombardia",
        )
        b = ScrapedDesignation(
            external_id="b",
            match_date="2026-10-10",
            championship="X",
            match_home="A",
            match_away="B",
            match_label="A - B",
            role="Arbitro",
            member_name="Mario Rossi",
            source="aia-figc-lombardia",
        )
        out = _dedupe_scraped_rows([a, b])
        assert len(out) == 2


class TestMatchKey:
    def test_key_from_home_away_fields(self):
        key = _designation_match_key(
            {
                "matchDate": "2026-05-24T12:00:00+00:00",
                "matchHome": "Milan SPA",
                "matchAway": "Arezzo",
                "role": "Arbitro",
                "memberName": "Gabriele Re Calegari",
            }
        )
        assert "2026-05-24" in key
        assert "gabriele re calegari" in key

    def test_identity_ignores_date(self):
        a = _designation_identity_key(
            {
                "matchDate": "2026-10-03",
                "matchHome": "Casa",
                "matchAway": "Ospite",
                "role": "Arbitro",
                "memberName": "Luca Bianchi",
            }
        )
        b = _designation_identity_key(
            {
                "matchDate": "2026-10-04",
                "matchHome": "Casa",
                "matchAway": "Ospite",
                "role": "Arbitro",
                "memberName": "Luca Bianchi",
            }
        )
        assert a == b


class TestNearDateKeepers:
    def test_purge_keeps_earliest(self):
        rows = [
            {
                "id": "late",
                "matchDate": "2026-10-04T12:00:00+00:00",
                "matchHome": "A",
                "matchAway": "B",
                "role": "Arbitro",
                "memberName": "Mario Rossi",
                "source": "aia-figc-lombardia",
            },
            {
                "id": "early",
                "matchDate": "2026-10-03T12:00:00+00:00",
                "matchHome": "A",
                "matchAway": "B",
                "role": "Arbitro",
                "memberName": "Mario Rossi",
                "source": "aia-figc-canc",
            },
        ]
        keepers, drop = _pick_near_date_keepers(
            rows,
            identity_fn=_designation_identity_key,
            date_fn=lambda r: _parse_match_day(r.get("matchDate")),
            sort_key_fn=lambda r: (
                _parse_match_day(r.get("matchDate")) or date.max,
                r.get("id", ""),
            ),
        )
        assert [k["id"] for k in keepers] == ["early"]
        assert [d["id"] for d in drop] == ["late"]


class TestSourcePriority:
    def test_lombardia_first(self):
        assert _source_priority("aia-figc-lombardia") < _source_priority(
            "aia-figc-toscana"
        )
