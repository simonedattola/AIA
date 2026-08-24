from app.member_roles import (
    member_matches_any_role_group,
    member_matches_role_group,
    normalize_role_groups,
    role_groups_member_query,
)


def test_normalize_role_groups():
    assert normalize_role_groups(["AE", "cds", "AE", "invalid"]) == ["AE", "cds"]
    assert normalize_role_groups(None) == []


def test_member_matches_role_group():
    ae = {"role": "AE", "memberRole": "arbitro"}
    assert member_matches_role_group(ae, "AE") is True
    assert member_matches_role_group(ae, "AA") is False
    cds = {
        "organigrammaKind": "cds",
        "memberRole": "consiglio_direttivo",
        "boardTitle": "Presidente",
    }
    assert member_matches_role_group(cds, "cds") is True


def test_member_matches_any_role_group():
    m = {"role": "AA", "memberRole": "assistente"}
    assert member_matches_any_role_group(m, ["AE", "AA"]) is True
    assert member_matches_any_role_group(m, ["AB"]) is False


def test_role_groups_member_query():
    q = role_groups_member_query(["AE", "cds"])
    assert "$or" in q
    assert {"role": {"$in": ["AE"]}} in q["$or"]
    assert {"organigrammaKind": {"$in": ["cds"]}} in q["$or"]
