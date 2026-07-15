from app.gallery_member_tags import member_ids_for_article, merge_member_ids


def test_merge_member_ids_dedupes():
    assert merge_member_ids(["a", "b"], ["b", "c"]) == ["a", "b", "c"]


def test_member_ids_for_article_uses_related_and_match():
    members = [
        {"id": "m1", "firstName": "Franco", "lastName": "Giardini"},
        {"id": "m2", "firstName": "Marco", "lastName": "Rossi"},
    ]
    article = {
        "title": "Raduno con Marco Rossi",
        "bodyHtml": "<p>Ospite anche Giardini Franco.</p>",
        "excerpt": "",
        "relatedMemberIds": ["m9"],
    }
    ids = member_ids_for_article(article, members)
    assert "m9" in ids
    assert "m2" in ids
    assert "m1" in ids
