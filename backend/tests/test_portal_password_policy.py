"""Portal password policy."""
from app.portal_password import validate_portal_password, default_portal_password


def test_validate_portal_password():
    assert validate_portal_password("short") is not None
    assert validate_portal_password("onlyletters") is not None
    assert validate_portal_password("12345678") is not None
    assert validate_portal_password("secure1pass") is None


def test_default_portal_password_normalizes():
    assert default_portal_password("Mario", "Rossi") == "mario.rossi"
    assert default_portal_password("Luca", "Bianchi") == "luca.bianchi"
