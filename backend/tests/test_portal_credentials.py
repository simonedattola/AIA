from app.portal_credentials import (
    fictitious_meccanografico_for_member,
    is_fictitious_meccanografico,
    is_invalid_meccanografico,
)


def test_fictitious_meccanografico_detected():
    member = {"id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "meccanografico": "A1B2C3D4"}
    assert fictitious_meccanografico_for_member(member) == "A1B2C3D4"
    assert is_fictitious_meccanografico(member)


def test_real_meccanografico_not_fictitious():
    member = {"id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "meccanografico": "12345678"}
    assert not is_fictitious_meccanografico(member)


def test_placeholder_a_is_invalid():
    member = {"id": "x", "meccanografico": "A"}
    assert is_invalid_meccanografico(member)
    assert is_invalid_meccanografico({**member, "meccanografico": "a"})
