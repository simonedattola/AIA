from app.article_categories import merge_categories, normalize_category


def test_merge_categories_dedupes_case_insensitive():
    merged = merge_categories(
        ["Vita sezionale", "Successi"],
        ["successi", "Eventi"],
        ["  Eventi  "],
    )
    assert merged == ["Vita sezionale", "Successi", "Eventi"]


def test_normalize_category():
    assert normalize_category("  Corso   arbitri  ") == "Corso arbitri"
