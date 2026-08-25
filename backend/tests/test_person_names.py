from app.person_names import format_person_name, format_person_name_parts


def test_all_caps_to_title():
    assert format_person_name("MARIO", "ROSSI") == "Mario Rossi"
    assert format_person_name(full="LORENZO ALESSIO") == "Lorenzo Alessio"


def test_already_mixed():
    assert format_person_name("Mario", "Rossi") == "Mario Rossi"


def test_parts():
    assert format_person_name_parts("MARIO", "DE ROSSI") == ("Mario", "De Rossi")


def test_italian_apostrophe_surnames():
    assert format_person_name("NICOLO'", "D'AZZEO") == "Nicolo' D'Azzeo"
    assert format_person_name("MATTEO", "DELL'ACQUA") == "Matteo Dell'Acqua"
    assert format_person_name("CHRISTIAN", "IANNO'") == "Christian Ianno'"
    assert format_person_name("NICOLO'", "LO GAGLIO") == "Nicolo' Lo Gaglio"
    assert format_person_name("GIUSEPPE GIOVANNI", "P. MARAGO'") == (
        "Giuseppe Giovanni P. Marago'"
    )
    assert format_person_name("FABIO", "RE FERRE'") == "Fabio Re Ferre'"
    assert format_person_name("ALESSANDRO FILIPPO", "ROMBOLA'") == (
        "Alessandro Filippo Rombola'"
    )


def test_curly_apostrophe_normalized():
    # U+2019 RIGHT SINGLE QUOTATION MARK
    assert format_person_name("MATTEO", "DELL\u2019ACQUA") == "Matteo Dell'Acqua"
    assert format_person_name("NICOLO\u2019", "D\u2019AZZEO") == "Nicolo' D'Azzeo"
