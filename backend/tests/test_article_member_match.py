from app.article_member_match import (
    apply_auto_related_members,
    linkify_member_names_in_html,
    match_members_by_full_name,
    merge_related_member_ids,
)


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


def test_match_cognome_nome_order():
    members = [
        {
            "id": "1",
            "firstName": "Franco",
            "lastName": "Giardini",
            "slug": "franco-giardini",
        }
    ]
    ids = match_members_by_full_name(
        "Comunicato",
        "<p>Presente Giardini Franco alla riunione.</p>",
        members,
    )
    assert ids == ["1"]


def test_apply_merges_manual_and_auto():
    members = [
        {"id": "1", "firstName": "Franco", "lastName": "Giardini"},
        {"id": "2", "firstName": "Marco", "lastName": "Rossi"},
    ]
    merged = apply_auto_related_members(
        {
            "title": "Franco Giardini in evidenza",
            "bodyHtml": "<p>Testo senza altri nomi.</p>",
            "relatedMemberIds": ["2"],
        },
        members,
    )
    assert merged == ["2", "1"]


def test_merge_related_member_ids_dedupes():
    assert merge_related_member_ids(["a", "b"], ["b", "c"]) == ["a", "b", "c"]


def test_linkify_member_names_in_html():
    members = [
        {
            "id": "1",
            "firstName": "Franco",
            "lastName": "Giardini",
            "slug": "franco-giardini",
        }
    ]
    html = "<p>Complimenti a Franco Giardini per la designazione.</p>"
    out = linkify_member_names_in_html(html, members)
    assert 'href="/arbitri/franco-giardini"' in out
    assert "Franco Giardini" in out
    assert 'data-member-link="1"' in out


def test_linkify_skips_existing_anchors():
    members = [
        {
            "id": "1",
            "firstName": "Franco",
            "lastName": "Giardini",
            "slug": "franco-giardini",
        }
    ]
    html = '<p>Vedi <a href="https://example.com">Franco Giardini</a> sul sito.</p>'
    out = linkify_member_names_in_html(html, members)
    assert out.count("franco-giardini") == 0
    assert "https://example.com" in out
