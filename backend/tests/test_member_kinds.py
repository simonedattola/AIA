from app.member_roles import (
    has_designations,
    infer_member_role,
    is_observer_designation_role,
    member_role_from_seed_category,
    member_role_label,
    normalize_member,
)


def test_member_role_from_seed():
    assert member_role_from_seed_category("Osservatore arbitrale") == "osservatore"
    assert member_role_from_seed_category("Eccellenza") == "arbitro"


def test_infer_legacy_kind():
    doc = {"kind": "oa", "firstName": "A", "lastName": "B"}
    normalize_member(doc)
    assert doc["memberRole"] == "osservatore"
    assert doc["observerType"] == "oa"


def test_has_designations():
    assert has_designations("arbitro")
    assert not has_designations("osservatore")


def test_observer_designation_role():
    assert is_observer_designation_role("Osservatore Arbitrale")


def test_member_role_label():
    assert "OA" in member_role_label("osservatore", "oa")


def test_chi_siamo_includes_arbitro_with_board_title():
    from app.member_roles import (
        chi_siamo_query,
        legacy_chi_siamo_query,
        legacy_arbitri_query,
        osservatori_query,
        is_arbitro_benemerito,
        has_organigramma_board_title,
    )

    q = chi_siamo_query()
    assert "boardTitle" in str(q)
    assert "benemerito" in str(q).lower()
    # Documento tipico doppio ruolo
    dual = {"memberRole": "arbitro", "boardTitle": "Area Informatica"}
    assert has_organigramma_board_title(dual)
    assert not has_organigramma_board_title({"boardTitle": "Arbitro Benemerito"})
    assert is_arbitro_benemerito({"role": "AB"})
    # Benemeriti restano nella lista arbitri; osservatori hanno query dedicata
    aq = legacy_arbitri_query()
    assert "arbitro" in str(aq)
    assert osservatori_query() == {"memberRole": "osservatore"}
    assert legacy_chi_siamo_query() == q


def test_normalize_president_not_revisione():
    doc = {
        "memberRole": "consiglio_direttivo",
        "boardTitle": "Organo di Revisione – Presidente",
        "isPresident": True,
    }
    normalize_member(doc)
    assert doc["isPresident"] is False

    prez = {
        "memberRole": "consiglio_direttivo",
        "boardTitle": "Presidente di Sezione",
    }
    normalize_member(prez)
    assert prez["isPresident"] is True


def test_dual_role_arbitro_keeps_designations():
    assert has_designations("arbitro")
    dual = {"memberRole": "arbitro", "boardTitle": "Area Informatica"}
    normalize_member(dual)
    assert dual["memberRole"] == "arbitro"
    assert has_designations(dual["memberRole"])
