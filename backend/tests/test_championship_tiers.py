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


def test_detect_under_youth_tiers():
    assert (
        detect_championship_tier("Under 14 Provinciali Calcio a 11 Maschile")
        == "Giovanissimi"
    )
    assert (
        detect_championship_tier("Under 15 Regionali Calcio a 11 Maschile")
        == "Giovanissimi"
    )
    assert (
        detect_championship_tier("Under 16 Provinciali Calcio a 11 Maschile")
        == "Allievi"
    )
    assert (
        detect_championship_tier("Under 17 Regionali Calcio a 11 Maschile") == "Allievi"
    )
    assert (
        detect_championship_tier("Under 18 Regionale Maschile Calcio a 11")
        == "Juniores"
    )
    assert detect_championship_tier("U15") == "Giovanissimi"
    assert detect_championship_tier("ALP") == "Allievi"  # sigla → Under 17
    assert detect_championship_tier("GIB") == "Giovanissimi"  # sigla → Under 14
    # Non confondere Under 17 Serie A-B con Serie A
    assert (
        detect_championship_tier(
            "Amichevole LND Campionato Nazionale Under 17 Serie A-B"
        )
        == "Allievi"
    )


def test_highest_from_under_designations():
    rows = [
        {
            "role": "Arbitro",
            "championship": "Under 14 Provinciali Calcio a 11 Maschile",
        },
        {
            "role": "Arbitro",
            "championship": "Under 17 Provinciali Calcio a 11 Maschile",
        },
        {"role": "Assistente 1", "championship": "Promozione"},
    ]
    assert highest_tier_from_designations(rows) == "Allievi"


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
    assert is_arbitro_designation_role("AE")
    assert is_arbitro_designation_role("AR")
    assert not is_arbitro_designation_role("Assistente 1")
    assert not is_arbitro_designation_role("AA1")


def test_is_womens_championship():
    assert is_womens_championship("ECCELLENZA FEMMINILE")
    assert is_womens_championship("Seconda Categoria Femm.")
    assert is_womens_championship("Under 15 Regionali Calcio a 11 Femminile")
    assert not is_womens_championship("ECCELLENZA")
    assert not is_womens_championship("SECONDA CATEGORIA")
    assert not is_womens_championship("Under 15 Regionali Calcio a 11 Maschile")


def test_highest_ignores_womens_competitions():
    rows = [
        {"role": "Arbitro", "championship": "SECONDA CATEGORIA"},
        {"role": "Arbitro", "championship": "ECCELLENZA FEMMINILE"},
        {"role": "Arbitro", "championship": "Under 15 Regionali Calcio a 11 Femminile"},
    ]
    assert highest_tier_from_designations(rows) == "Seconda Categoria"
