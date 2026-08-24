"""Tests for championship acronym expansion and AIA Att. role codes."""

from app.championship_codes import (
    CHAMPIONSHIP_CODES,
    expand_championship_label,
    resolve_att_role,
)
from app.championship_tiers import detect_championship_tier, is_womens_championship
from app.designations_import import parse_designations_file, _normalize_role


class TestExpandChampionshipLabel:
    def test_sec(self):
        assert expand_championship_label("SEC") == "Seconda Categoria"

    def test_pri_case_insensitive(self):
        assert expand_championship_label("pri") == "Prima Categoria"

    def test_full_name_unchanged(self):
        assert expand_championship_label("SECONDA CATEGORIA") == "SECONDA CATEGORIA"

    def test_all_user_codes_present(self):
        expected = {
            "PRI", "SEC", "TER", "FED", "FEP", "CP1", "CR2", "CRJ", "FCR",
            "JUR", "JRB", "JUP", "R18", "ALR", "ALP", "ARB", "ALB",
            "GIR", "GIP", "GRB", "GIB", "CGB", "ARF", "GIF",
            "ECC", "PRO", "JUN", "GIN", "ALA",
        }
        assert expected <= set(CHAMPIONSHIP_CODES)


class TestAttRole:
    def test_ae(self):
        assert resolve_att_role("AE") == "Arbitro"
        assert _normalize_role("AE") == "Arbitro"

    def test_aa(self):
        assert resolve_att_role("AA") == "Assistente 1"
        assert _normalize_role("AA") == "Assistente 1"

    def test_ar_aa1_aa2(self):
        assert resolve_att_role("AR") == "Arbitro"
        assert resolve_att_role("AA1") == "Assistente 1"
        assert resolve_att_role("AA2") == "Assistente 2"
        assert _normalize_role("AA2") == "Assistente 2"


class TestTierFromCodes:
    def test_sec_tier(self):
        assert detect_championship_tier("SEC") == "Seconda Categoria"

    def test_pri_tier(self):
        assert detect_championship_tier("PRI") == "Prima Categoria"

    def test_fed_is_womens(self):
        assert is_womens_championship("FED")


class TestFormatBImport:
    def test_format_b_headers(self):
        content = (
            "Data / Ora;Cat.;Gir.;Giorn.;Num. Gara;Sq. Locale;Sq. Ospite;Impianto;Att.;Associato\n"
            "17/05/2026 15:30;SEC;R;1;12345;PRO JUVENTUTE ASD;MAZZO 80 A.C.;Campo A;AE;Menapace Lorenzo\n"
            "17/05/2026 15:30;SEC;R;1;12345;PRO JUVENTUTE ASD;MAZZO 80 A.C.;Campo A;AA;Rossi Marco\n"
        ).encode("utf-8")
        rows, warnings, meta = parse_designations_file(content, "export.csv")
        assert len(rows) == 2
        assert rows[0]["matchDate"] == "2026-05-17"
        assert rows[0]["championship"] == "Seconda Categoria"
        assert rows[0]["girone"] == "R"
        assert rows[0]["matchDay"] == "1"
        assert rows[0]["matchHome"] == "PRO JUVENTUTE ASD"
        assert rows[0]["matchAway"] == "MAZZO 80 A.C."
        assert rows[0]["role"] == "Arbitro"
        assert rows[0]["memberName"] == "Menapace Lorenzo"
        assert rows[1]["role"] == "Assistente 1"
        assert rows[1]["memberName"] == "Rossi Marco"
        # Num. Gara must not become matchLabel
        assert "12345" not in rows[0]["matchLabel"]

    def test_format_a_with_associato(self):
        content = (
            "Att.;Data;Categoria;Giron.;Squadra Locale;Squadra Ospite;Associato;Ris.;Stato;Rimb.\n"
            "AE;17/05/2026;PRI;A;Casa FC;Ospite FC;Luca Bianchi;2-1;;\n"
        ).encode("utf-8")
        rows, warnings, _ = parse_designations_file(content, "storico.csv")
        assert len(rows) == 1
        assert rows[0]["championship"] == "Prima Categoria"
        assert rows[0]["role"] == "Arbitro"
        assert rows[0]["memberName"] == "Luca Bianchi"

    def test_continuation_rows_same_match(self):
        # Prima riga = gara completa; righe successive solo Att. + Associato (Cognome Nome)
        content = (
            'Data / Ora;Cat.;Gir.;Giorn.;Num. Gara;Sq. Locale;Sq. Ospite;Impianto;Att.;Associato\n'
            '"21/03/2026\n15:00";GIN;;0;1;INTERNAZIONALE MILANO S.P.A.;JACKSONVILLE FC;MILANO/AFFORI;AA2;LORENZO ALESSIO\n'
            ";;;;;;;;AR;MENAPACE LORENZO\n"
            ";;;;;;;;AA1;GIORGI FABRIZIO\n"
        ).encode("utf-8")
        rows, warnings, meta = parse_designations_file(content, "designazioni.csv")
        assert len(rows) == 3
        assert rows[0]["matchDate"] == "2026-03-21"
        assert rows[0]["championship"] == "Amichevole LND Giovanissimi Nazionali"
        assert rows[0]["matchHome"] == "INTERNAZIONALE MILANO S.P.A."
        assert rows[0]["matchAway"] == "JACKSONVILLE FC"
        assert rows[0]["role"] == "Assistente 2"
        assert rows[0]["memberName"] == "LORENZO ALESSIO"
        assert rows[1]["matchDate"] == "2026-03-21"
        assert rows[1]["matchHome"] == "INTERNAZIONALE MILANO S.P.A."
        assert rows[1]["role"] == "Arbitro"
        assert rows[1]["memberName"] == "MENAPACE LORENZO"
        assert rows[2]["role"] == "Assistente 1"
        assert rows[2]["memberName"] == "GIORGI FABRIZIO"
        assert all(r["matchAway"] == "JACKSONVILLE FC" for r in rows)

    def test_multiline_date_cell(self):
        from app.designations_import import _parse_date

        assert _parse_date("21/03/2026\n15:00") == "2026-03-21"
        assert _parse_date("21/03/2026 15:00") == "2026-03-21"
        content = (
            "Att.;Data;Categoria;Giron.;Squadra Locale;Squadra Ospite;Ris.;Voto OA;Voto OT;Stato;Rimb.\n"
            "AE;17/05/2026;SEC;R;Casa FC;Ospite FC;1-0;;;;\n"
        ).encode("utf-8")
        try:
            parse_designations_file(content, "storico.csv")
            assert False, "expected ValueError"
        except ValueError as e:
            assert "Nessuna designazione valida" in str(e)

    def test_template_csv_parses(self):
        from app.designations_import import IMPORT_TEMPLATE_CSV

        rows, warnings, _ = parse_designations_file(
            IMPORT_TEMPLATE_CSV.encode("utf-8"), "modello.csv"
        )
        assert len(rows) == 2
        assert rows[0]["championship"] == "Seconda Categoria"
        assert rows[0]["role"] == "Arbitro"
