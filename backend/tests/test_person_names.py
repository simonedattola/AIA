from app.person_names import format_person_name, format_person_name_parts


def test_all_caps_to_title():
    assert format_person_name("MARIO", "ROSSI") == "Mario Rossi"
    assert format_person_name(full="LORENZO ALESSIO") == "Lorenzo Alessio"


def test_already_mixed():
    assert format_person_name("Mario", "Rossi") == "Mario Rossi"


def test_parts():
    assert format_person_name_parts("MARIO", "DE ROSSI") == ("Mario", "De Rossi")
