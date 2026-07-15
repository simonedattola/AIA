"""Dedup designazioni: stessa gara su hub diversi."""
from app.designations_sync import _dedupe_scraped_rows, _designation_match_key, _source_priority
from app.scrapers.aia_lombardia import ScrapedDesignation, _external_id


class TestExternalId:
    def test_same_match_different_gare_same_id(self):
        a = _external_id("2026-05-24", "Milan SPA", "Arezzo", "Arbitro", "Gabriele Re Calegari")
        b = _external_id("2026-05-24", "Milan SPA", "Arezzo", "Arbitro", "Gabriele Re Calegari")
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


class TestMatchKey:
    def test_key_from_home_away_fields(self):
        key = _designation_match_key({
            "matchDate": "2026-05-24T12:00:00+00:00",
            "matchHome": "Milan SPA",
            "matchAway": "Arezzo",
            "role": "Arbitro",
            "memberName": "Gabriele Re Calegari",
        })
        assert "2026-05-24" in key
        assert "gabriele re calegari" in key


class TestSourcePriority:
    def test_lombardia_first(self):
        assert _source_priority("aia-figc-lombardia") < _source_priority("aia-figc-toscana")
