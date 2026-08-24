"""Unit tests for designation sync member resolution."""

from app.designations_sync import (
    _split_full_name,
    _split_full_name_cognome_nome,
    _normalize_name,
    _name_match_keys,
    _lookup_member_info,
)


class TestSplitFullName:
    def test_two_parts(self):
        assert _split_full_name("Lorenzo Menapace") == ("Lorenzo", "Menapace")

    def test_three_parts(self):
        assert _split_full_name("Francesca Maria Conti") == ("Francesca Maria", "Conti")

    def test_single_name(self):
        assert _split_full_name("Madonna") == ("Madonna", "")


class TestSplitCognomeNome:
    def test_two_parts(self):
        assert _split_full_name_cognome_nome("Menapace Lorenzo") == ("Lorenzo", "Menapace")

    def test_compound_given_name(self):
        assert _split_full_name_cognome_nome("Conti Francesca Maria") == (
            "Francesca Maria",
            "Conti",
        )


class TestNormalizeName:
    def test_lowercase_strip(self):
        assert _normalize_name("  Mario  Rossi ") == "mario rossi"


class TestNameMatchKeys:
    def test_reverses_two_tokens(self):
        keys = _name_match_keys("Rossi Mario")
        assert "rossi mario" in keys
        assert "mario rossi" in keys

    def test_lookup_cognome_nome_against_anagrafica(self):
        lookup = {
            "mario rossi": {
                "id": "m1",
                "slug": "mario-rossi",
                "firstName": "Mario",
                "lastName": "Rossi",
            }
        }
        # Index also reversed as build_member_lookup would
        lookup["rossi mario"] = lookup["mario rossi"]
        info = _lookup_member_info(lookup, "Rossi Mario")
        assert info["id"] == "m1"
        assert info["slug"] == "mario-rossi"
