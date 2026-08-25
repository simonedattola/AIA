"""Tests for flexible file import of designations."""

import pytest

from app.designations_import import (
    parse_designations_file,
    _normalize_role,
    _parse_date,
    _split_match_label,
    _dedupe_rows,
)


class TestParseDate:
    def test_iso(self):
        assert _parse_date("2026-05-17") == "2026-05-17"

    def test_italian(self):
        assert _parse_date("17/05/2026") == "2026-05-17"


class TestNormalizeRole:
    def test_arbitro(self):
        assert _normalize_role("arbitro") == "Arbitro"

    def test_assistente_generico(self):
        # Ruolo generico: non forzare "Assistente 1" (resta la label importata)
        assert _normalize_role("Assistente") == "Assistente"


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
        content = (
            "Data;Campionato;Squadra casa;Squadra ospite;Ruolo;Nominativo\n"
            "17/05/2026;SECONDA;Casa FC;Ospite FC;Arbitro;Mario Rossi\n"
        ).encode("utf-8")
        rows, warnings, meta = parse_designations_file(content, "designazioni.csv")
        assert len(rows) == 1
        assert rows[0]["memberName"] == "Mario Rossi"
        assert rows[0]["matchDate"] == "2026-05-17"
        assert meta["columnMaps"]


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
            "2026-05-16;C - D;Arbitro;Luca Bianchi\n"
        ).encode("utf-8")
        rows, warnings, _ = parse_designations_file(content, "designazioni.csv")
        assert len(rows) == 1
        assert rows[0]["memberName"] == "Luca Bianchi"
        assert any("Osservatore" in w or "osservatore" in w.lower() for w in warnings)

    def test_template_is_valid(self):
        # Template ufficiale: colonna "gara" evita ambiguità header detection
        # (ruolo "Arbitro" non deve essere scambiato per intestazione nominativo).
        content = (
            "data;gara;ruolo;nominativo\n"
            "2026-05-17;PRO JUVENTUTE ASD - MAZZO 80 A.C.;Arbitro;Lorenzo Menapace\n"
            "2026-05-17;PRO JUVENTUTE ASD - MAZZO 80 A.C.;Assistente 1;Marco Rossi\n"
        ).encode("utf-8")
        rows, warnings, _ = parse_designations_file(content, "modello.csv")
        assert len(rows) == 2
        assert not warnings

    def test_empty_file_raises(self):
        with pytest.raises(ValueError, match="Nessuna designazione valida"):
            parse_designations_file(
                "data;gara;ruolo;nominativo\n".encode("utf-8"), "vuoto.csv"
            )

    def test_duplicate_rows_in_csv(self):
        content = (
            "data;gara;ruolo;nominativo\n"
            "2026-05-16;A - B;Arbitro;Luca Bianchi\n"
            "2026-05-16;A - B;Arbitro;Luca Bianchi\n"
        ).encode("utf-8")
        rows, warnings, _ = parse_designations_file(content, "dup.csv")
        assert len(rows) == 1
        assert any("duplicate" in w.lower() for w in warnings)


class TestTitleCaseOnImport:
    def test_canonical_display_name_from_all_caps(self):
        from app.designations_import import _canonical_member_display_name

        assert _canonical_member_display_name("MARIO", "ROSSI") == "Mario Rossi"
        assert (
            _canonical_member_display_name(fallback="MENAPACE LORENZO")
            == "Menapace Lorenzo"
        )
        assert (
            _canonical_member_display_name(fallback="NICOLO' D'AZZEO")
            == "Nicolo' D'Azzeo"
        )

    @pytest.mark.asyncio
    async def test_file_import_saves_title_case_not_all_caps(self):
        """Dry-run preview + write path: nomi file MAIUSCOLI → title case."""
        from app.db import get_db
        from app.designations_import import import_designations_from_file
        from app.models import _id
        from app.person_names import format_person_name_parts

        preview_csv = (
            "data;gara;ruolo;nominativo\n"
            "2026-05-16;Legnano - Castellanza;Arbitro;MENAPACE LORENZO\n"
            "2026-05-16;Legnano - Castellanza;Assistente 1;GIORGI FABRIZIO\n"
        ).encode("utf-8")
        preview = await import_designations_from_file(
            preview_csv, "caps.csv", dry_run=True
        )
        names = [p["memberName"] for p in preview["preview"]]
        assert len(names) == 2
        assert all(n != n.upper() for n in names if n)

        unique = _id()[:10].upper()
        last_raw = f"ZZIMPORT{unique}"
        first_raw = "LORENZO"
        full_caps = f"{last_raw} {first_raw}"
        content = (
            "data;gara;ruolo;nominativo\n"
            f"2099-01-15;Casa Zzimp - Ospite Zzimp;Arbitro;{full_caps}\n"
        ).encode("utf-8")
        result = await import_designations_from_file(
            content, "create-caps.csv", dry_run=False
        )
        assert (
            result["inserted"] >= 1
            or result["updated"] >= 1
            or result.get("membersCreated", 0) >= 1
        )
        db = get_db()
        des = await db.designations.find_one(
            {
                "memberName": {"$regex": last_raw, "$options": "i"},
                "matchDate": {"$regex": "^2099-01-15"},
            },
            {"_id": 0, "memberName": 1, "memberId": 1},
        )
        assert des is not None
        expect_first, expect_last = format_person_name_parts("Lorenzo", last_raw)
        assert des["memberName"] == f"{expect_first} {expect_last}"
        assert des["memberName"] != full_caps
        mid = des.get("memberId")
        try:
            if mid:
                m = await db.members.find_one(
                    {"id": mid}, {"_id": 0, "firstName": 1, "lastName": 1}
                )
                assert m is not None
                assert m["firstName"] == expect_first
                assert m["lastName"] == expect_last
                assert m["firstName"] != first_raw
        finally:
            if mid:
                await db.designations.delete_many({"memberId": mid})
                await db.members.delete_one({"id": mid})
            else:
                await db.designations.delete_many(
                    {
                        "matchDate": {"$regex": "^2099-01-15"},
                        "matchLabel": "Casa Zzimp - Ospite Zzimp",
                    }
                )
