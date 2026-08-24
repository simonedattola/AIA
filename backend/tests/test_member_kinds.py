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


def test_aa_is_assistente_arbitrale():
    from app.member_roles import infer_member_role, member_role_label, normalize_member
    from app.members_import import _normalize_member_role

    assert _normalize_member_role("AA")[0] == "assistente"
    assert infer_member_role({"role": "AA"}) == "assistente"
    doc = {"role": "AA", "firstName": "Marco", "lastName": "Test"}
    normalize_member(doc)
    assert doc["memberRole"] == "assistente"
    assert member_role_label(doc["memberRole"], doc=doc) == "Assistente Arbitrale"


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
    assert doc["organigrammaKind"] == "ors"

    prez = {
        "memberRole": "consiglio_direttivo",
        "organigrammaKind": "cds",
        "boardTitle": "Presidente di Sezione",
    }
    normalize_member(prez)
    assert prez["isPresident"] is True

    vice = {
        "organigrammaKind": "cds",
        "boardTitle": "Vice Presidente — Area designazioni",
        "isPresident": True,
    }
    normalize_member(vice)
    assert vice["isPresident"] is False

    # OA + Presidente CDS: qualifica da codice AIA, presidente da incarico
    zambon = {
        "role": "OA",
        "memberRole": "consiglio_direttivo",
        "boardTitle": "Presidente di Sezione — Codice Etico",
        "isPresident": False,
    }
    normalize_member(zambon)
    assert zambon["memberRole"] == "osservatore"
    assert zambon["organigrammaKind"] == "cds"
    assert zambon["isPresident"] is True


def test_dual_role_arbitro_keeps_designations():
    assert has_designations("arbitro")
    dual = {"memberRole": "arbitro", "role": "AE", "boardTitle": "Area Informatica"}
    normalize_member(dual)
    assert dual["memberRole"] == "arbitro"
    assert dual["organigrammaKind"] == "collaboratore"
    assert has_designations(dual["memberRole"])


def test_category_only_ae_aa():
    from app.member_roles import can_have_max_category

    assert can_have_max_category({"role": "AE"})
    assert can_have_max_category({"role": "AA"})
    assert not can_have_max_category({"role": "AB"})
    assert not can_have_max_category({"role": "OA"})
    assert not can_have_max_category({"role": "AFR"})
    # Sync AIA senza codice: role testuale + memberRole
    assert can_have_max_category({"role": "Arbitro", "memberRole": "arbitro"})
    assert can_have_max_category({"memberRole": "assistente"})
    assert not can_have_max_category({"role": "Arbitro", "memberRole": "osservatore"})
