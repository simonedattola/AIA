"""Tests for flexible file import of designations."""
import pytest

from app.designations_import import (
    IMPORT_TEMPLATE_CSV,
    parse_designations_file,
    _normalize_role,
    _parse_date,
    _split_match_label,
    _dedupe_rows,
    _map_columns,
)
import pandas as pd


class TestParseDate:
    def test_iso(self):
        assert _parse_date("2026-05-17") == "2026-05-17"

    def test_italian(self):
        assert _parse_date("17/05/2026") == "2026-05-17"


class TestNormalizeRole:
    def test_arbitro(self):
        assert _normalize_role("arbitro") == "Arbitro"

    def test_assistente_generico(self):
        assert _normalize_role("Assistente") == "Assistente 1"


class TestSplitMatchLabel:
    def test_dash(self):
        assert _split_match_label("Legnano - Castellanza") == ("Legnano", "Castellanza")


class TestColumnMapping:
    def test_reordered_columns(self):
        content = (
            "nominativo;ruolo;data;partita\n"
            "Luca Bianchi;Arbitro;2026-05-16;Legnano - Castellanza\n"
        ).encode("utf-8")
        rows, warnings, meta = parse_designations_file(content, "designazioni.csv")
        assert len(rows) == 1
        assert rows[0]["memberName"] == "Luca Bianchi"
        assert rows[0]["matchLabel"] == "Legnano - Castellanza"
        assert meta["fileType"] == "csv"

    def test_alternate_headers(self):
        df = pd.DataFrame(
            [
                ["17/05/2026", "SECONDA", "Casa FC", "Ospite FC", "Arbitro", "Mario Rossi"],
            ],
            columns=["Giorno", "Campionato", "Squadra casa", "Squadra ospite", "Incarico", "Designato"],
        )
        mapped, col_map, _ = _map_columns(df)
        assert "matchDate" in mapped.columns
        assert "memberName" in mapped.columns
        assert col_map.get("matchDate")


class TestDedupeRows:
    def test_skips_duplicate_in_file(self):
        row = {
            "matchDate": "2026-05-16",
            "matchHome": "A",
            "matchAway": "B",
            "matchLabel": "A - B",
            "role": "Arbitro",
            "memberName": "Luca Bianchi",
        }
        out, skipped = _dedupe_rows([row, row])
        assert len(out) == 1
        assert skipped == 1


class TestParseDesignationsFile:
    def test_csv_semicolon(self):
        content = (
            "data;gara;ruolo;nominativo\n"
            "2026-05-16;Legnano Juniores - Castellanza;Arbitro;Luca Bianchi\n"
        ).encode("utf-8")
        rows, warnings, _ = parse_designations_file(content, "designazioni.csv")
        assert len(rows) == 1
        assert rows[0]["matchDate"] == "2026-05-16"
        assert rows[0]["matchLabel"] == "Legnano Juniores - Castellanza"
        assert rows[0]["memberName"] == "Luca Bianchi"
        assert warnings == []

    def test_skips_observer(self):
        content = (
            "data;gara;ruolo;nominativo\n"
            "2026-05-16;A - B;Osservatore;Giovanni Ferri\n"
        ).encode("utf-8")
        rows, warnings, _ = parse_designations_file(content, "designazioni.csv")
        assert rows == []
        assert any("Osservatore" in w for w in warnings)

    def test_template_is_valid(self):
        rows, warnings, _ = parse_designations_file(IMPORT_TEMPLATE_CSV.encode("utf-8"), "modello.csv")
        assert len(rows) == 2
        assert not warnings

    def test_empty_file_raises(self):
        with pytest.raises(ValueError, match="Nessuna designazione valida"):
            parse_designations_file("data;gara;ruolo;nominativo\n".encode("utf-8"), "vuoto.csv")

    def test_duplicate_rows_in_csv(self):
        content = (
            "data;gara;ruolo;nominativo\n"
            "2026-05-16;A - B;Arbitro;Luca Bianchi\n"
            "2026-05-16;A - B;Arbitro;Luca Bianchi\n"
        ).encode("utf-8")
        rows, warnings, _ = parse_designations_file(content, "dup.csv")
        assert len(rows) == 1
        assert any("duplicate" in w.lower() for w in warnings)
