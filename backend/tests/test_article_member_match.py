from app.article_member_match import match_members_by_full_name


def test_match_full_name_only():
    members = [
        {"id": "1", "firstName": "Franco", "lastName": "Giardini"},
        {"id": "2", "firstName": "Marco", "lastName": "Rossi"},
    ]
    ids = match_members_by_full_name(
        "Cordoglio per Franco Giardini",
        "<p>Il nostro associato Franco Giardini è mancato.</p>",
        members,
    )
    assert ids == ["1"]

    ids2 = match_members_by_full_name(
        "Notizie sezionali",
        "<p>Giardini era un grande arbitro.</p>",
        members,
    )
    assert ids2 == []
