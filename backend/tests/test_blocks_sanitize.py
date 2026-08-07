from app.blocks_sanitize import normalize_instagram_embed_html, sanitize_block


def test_normalize_instagram_embed_from_blockquote():
    html = (
        '<blockquote class="instagram-media" data-instgrm-permalink='
        '"https://www.instagram.com/p/DW1XFlpjGQV/?utm_source=ig_embed">'
        '</blockquote><script async src="//www.instagram.com/embed.js"></script>'
    )
    out = normalize_instagram_embed_html(html)
    assert out is not None
    assert "instagram.com/p/DW1XFlpjGQV/embed/captioned" in out
    assert "<iframe" in out


def test_normalize_instagram_embed_from_plain_url():
    out = normalize_instagram_embed_html("https://www.instagram.com/p/DW1XFlpjGQV/")
    assert out is not None
    assert "DW1XFlpjGQV" in out


def test_sanitize_embed_block_converts_instagram():
    block = {
        "type": "embed",
        "config": {"html": "https://www.instagram.com/p/DW1XFlpjGQV/"},
    }
    sanitized = sanitize_block(block)
    assert "iframe" in sanitized["config"]["html"]
    assert "embed.js" not in sanitized["config"]["html"]
