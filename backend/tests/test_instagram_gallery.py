from app.instagram_gallery import (
    is_designation_post,
    is_unsuitable_for_gallery,
    parse_instagram_username,
)


def test_parse_instagram_username():
    assert (
        parse_instagram_username("https://www.instagram.com/aia_legnano/")
        == "aia_legnano"
    )
    assert parse_instagram_username("@aia_legnano") == "aia_legnano"


def test_is_designation_post():
    assert is_designation_post(
        "Ecco le partite di questo fine settimana #aialegnano #designazioni"
    )
    assert is_designation_post("Domenica calda per i nostri associati #designazioni")
    assert not is_designation_post("4 NUOVI GIOVANI ASSOCIATI PER LA NOSTRA SEZIONE!")
    assert not is_designation_post("Anita Costa intervistata a Radio Materia")


def test_is_unsuitable_for_gallery():
    assert is_unsuitable_for_gallery("Quiz time! #quiztime", product_type="feed")
    assert is_unsuitable_for_gallery("", media_type=2, product_type="clips")
    assert not is_unsuitable_for_gallery(
        "Raduno playoff CAN D a Peschiera", media_type=1, product_type="feed"
    )
