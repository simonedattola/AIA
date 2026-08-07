from app.championship_tiers import (
    detect_championship_tier,
    highest_tier_from_designations,
    is_arbitro_designation_role,
    is_womens_championship,
)


def test_detect_tiers():
    assert (
        detect_championship_tier("SECONDA CATEGORIA · Girone R") == "Seconda Categoria"
    )
    assert detect_championship_tier("Serie D") == "Serie D"
    assert detect_championship_tier("ECCELLENZA") == "Eccellenza"


def test_highest_from_designations():
    rows = [
        {"role": "Arbitro", "championship": "SECONDA CATEGORIA"},
        {"role": "Assistente 1", "championship": "Serie A"},
        {"role": "Arbitro", "championship": "PROMOZIONE"},
    ]
    assert highest_tier_from_designations(rows) == "Promozione"


def test_higher_tier_wins():
    rows = [
        {"role": "Arbitro", "championship": "Terza Categoria"},
        {"role": "Arbitro", "championship": "Serie C"},
    ]
    assert highest_tier_from_designations(rows) == "Serie C"


def test_arbitro_role_only():
    assert is_arbitro_designation_role("Arbitro")
    assert not is_arbitro_designation_role("Assistente 1")


def test_is_womens_championship():
    assert is_womens_championship("ECCELLENZA FEMMINILE")
    assert is_womens_championship("Seconda Categoria Femm.")
    assert not is_womens_championship("ECCELLENZA")
    assert not is_womens_championship("SECONDA CATEGORIA")


def test_highest_ignores_womens_competitions():
    rows = [
        {"role": "Arbitro", "championship": "SECONDA CATEGORIA"},
        {"role": "Arbitro", "championship": "ECCELLENZA FEMMINILE"},
    ]
    assert highest_tier_from_designations(rows) == "Seconda Categoria"
