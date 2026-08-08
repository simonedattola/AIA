from app.designation_enrich import (
    enrich_designation,
    enrich_testimonial,
    build_member_lookups,
    _parse_category_string,
)


def test_parse_category_string():
    parsed = _parse_category_string("SECONDA CATEGORIA · Girone R · Giornata 12")
    assert "SECONDA" in parsed["championship"]
    assert parsed["girone"] == "R"
    assert parsed["matchDay"] == "12"


def test_enrich_fills_slug_and_fields():
    members = [
        {
            "id": "m1",
            "slug": "luca-bianchi",
            "firstName": "Luca",
            "lastName": "Bianchi",
        },
    ]
    slug_by_id, member_by_name = build_member_lookups(members)
    item = {
        "memberName": "Luca Bianchi",
        "category": "PROMOZIONE · Girone A · Giornata 3",
        "matchHome": "A",
        "matchAway": "B",
    }
    enrich_designation(item, slug_by_id, member_by_name)
    assert item["memberSlug"] == "luca-bianchi"
    assert item["memberId"] == "m1"
    assert item["championship"]
    assert item["girone"] == "A"
    assert item["matchDay"] == "3"
    assert item["matchLabel"] == "A - B"


def test_enrich_testimonial_by_member_id_and_name():
    members = [
        {
            "id": "m1",
            "slug": "simone-dattola",
            "firstName": "Simone",
            "lastName": "Dattola",
            "memberRole": "arbitro",
            "photoUrl": "/api/uploads/simone.jpg",
        },
    ]
    slug_by_id, member_by_name = build_member_lookups(members, arbitri_only=False)
    member_by_id = {"m1": members[0]}

    by_id = {"name": "Simone Dattola", "memberId": "m1", "quote": "x"}
    enrich_testimonial(by_id, slug_by_id, member_by_name, member_by_id)
    assert by_id["memberSlug"] == "simone-dattola"
    assert by_id["photoUrl"] == "/api/uploads/simone.jpg"

    by_name = {"name": "Simone Dattola", "quote": "y"}
    enrich_testimonial(by_name, slug_by_id, member_by_name, member_by_id)
    assert by_name["memberSlug"] == "simone-dattola"
    assert by_name["memberId"] == "m1"
    assert by_name["photoUrl"] == "/api/uploads/simone.jpg"
