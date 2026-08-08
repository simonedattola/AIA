"""Tests for flexible members file import."""

import pytest

from app.members_import import (
    IMPORT_TEMPLATE_CSV,
    parse_members_file,
    _split_full_name,
    _normalize_member_role,
    _dedupe_rows,
    _map_columns,
)
import pandas as pd


class TestSplitName:
    def test_two_parts(self):
        assert _split_full_name("Mario Rossi") == ("Mario", "Rossi")

    def test_three_parts(self):
        assert _split_full_name("Francesca Maria Conti") == ("Francesca Maria", "Conti")


class TestNormalizeRole:
    def test_arbitro(self):
        assert _normalize_member_role("Arbitro")[0] == "arbitro"

    def test_assistente(self):
        assert _normalize_member_role("Assistente")[0] == "assistente"


class TestParseMembersFile:
    def test_standard_csv(self):
        content = (
            "nome;cognome;ruolo;categoria;meccanografico\n"
            "Mario;Rossi;Arbitro;;12345\n"
        ).encode("utf-8")
        rows, warnings, meta = parse_members_file(content, "anagrafica.csv")
        assert len(rows) == 1
        assert rows[0]["firstName"] == "Mario"
        assert rows[0]["lastName"] == "Rossi"
        assert rows[0]["category"] == ""
        assert rows[0]["meccanografico"] == "12345"

    def test_nominativo_column(self):
        content = (
            "nominativo;ruolo;email\n" "Sara Bianchi;Assistente;sara@test.it\n"
        ).encode("utf-8")
        rows, _, _ = parse_members_file(content, "anagrafica.csv")
        assert rows[0]["firstName"] == "Sara"
        assert rows[0]["lastName"] == "Bianchi"

    def test_reordered_columns(self):
        content = (
            "meccanografico;ruolo;cognome;nome\n" "99999;Arbitro;Verdi;Luigi\n"
        ).encode("utf-8")
        rows, _, _ = parse_members_file(content, "anagrafica.csv")
        assert rows[0]["firstName"] == "Luigi"
        assert rows[0]["meccanografico"] == "99999"

    def test_no_category_ok(self):
        content = ("nome;cognome;ruolo\n" "Anna;Neri;Arbitro\n").encode("utf-8")
        rows, _, _ = parse_members_file(content, "anagrafica.csv")
        assert rows[0]["category"] == ""

    def test_template(self):
        rows, warnings, _ = parse_members_file(
            IMPORT_TEMPLATE_CSV.encode("utf-8"), "modello.csv"
        )
        assert len(rows) == 2
        assert not warnings

    def test_duplicate_in_file(self):
        content = (
            "nome;cognome;ruolo\n" "Mario;Rossi;Arbitro\n" "Mario;Rossi;Arbitro\n"
        ).encode("utf-8")
        rows, warnings, _ = parse_members_file(content, "dup.csv")
        assert len(rows) == 1
        assert any("duplicate" in w.lower() for w in warnings)

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="Nessun associato valido"):
            parse_members_file("nome;cognome;ruolo\n".encode("utf-8"), "vuoto.csv")


class TestDedupeRows:
    def test_by_name(self):
        row = {
            "firstName": "Mario",
            "lastName": "Rossi",
            "email": "",
            "meccanografico": "",
        }
        out, skipped = _dedupe_rows([row, row])
        assert len(out) == 1
        assert skipped == 1
