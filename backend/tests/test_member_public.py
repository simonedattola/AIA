"""Member serialization must never leak password hashes."""
from app.member_roles import public_member, strip_sensitive_member_fields


def test_public_member_strips_secrets():
    doc = {
        "id": "1",
        "firstName": "Mario",
        "lastName": "Rossi",
        "memberRole": "arbitro",
        "passwordHash": "$2b$12$secret",
        "meccanografico": "12345",
        "notes": "privato",
        "email": "mario@example.com",
        "emailVisibile": False,
        "phone": "333",
        "telefonoVisibile": True,
    }
    out = public_member(doc)
    assert "passwordHash" not in out
    assert "meccanografico" not in out
    assert "notes" not in out
    assert out["email"] == ""
    assert out["phone"] == "333"


def test_strip_sensitive_member_fields():
    doc = {"passwordHash": "x", "firstName": "A"}
    strip_sensitive_member_fields(doc)
    assert "passwordHash" not in doc
    assert doc["firstName"] == "A"
