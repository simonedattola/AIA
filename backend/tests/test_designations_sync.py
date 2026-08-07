"""Unit tests for designation sync member resolution."""

from app.designations_sync import _split_full_name, _normalize_name


class TestSplitFullName:
    def test_two_parts(self):
        assert _split_full_name("Lorenzo Menapace") == ("Lorenzo", "Menapace")

    def test_three_parts(self):
        assert _split_full_name("Francesca Maria Conti") == ("Francesca Maria", "Conti")

    def test_single_name(self):
        assert _split_full_name("Madonna") == ("Madonna", "")


class TestNormalizeName:
    def test_lowercase_strip(self):
        assert _normalize_name("  Mario  Rossi ") == "mario rossi"
