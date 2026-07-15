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
