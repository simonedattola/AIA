"""Test normalizzazione gallerie BWG negli articoli."""
from app.article_body import normalize_article_body_html


def test_bwg_gallery_becomes_carousel():
    html = """
    <p>Testo introduttivo.</p>
    <style id="bwg-style-0">#bwg { color: red; }</style>
    <div class="bwg_container" id="bwg_container1_0">
      <img src="/api/uploads/a.jpg" alt="uno"/>
      <img src="/api/uploads/b.jpg" alt="due"/>
      <div class="pagination-links"><a title="Vai alla pagina successiva">›</a></div>
    </div>
    """
    out = normalize_article_body_html(html)
    assert "bwg_container" not in out
    assert "pagination-links" not in out
    assert "aia-article-carousel" in out
    assert "/api/uploads/a.jpg" in out
    assert "/api/uploads/b.jpg" in out


def test_single_image_unchanged():
    html = '<p>Hello</p><p><img src="/x.jpg" alt=""/></p>'
    out = normalize_article_body_html(html)
    assert "aia-article-carousel" not in out
    assert "/x.jpg" in out
