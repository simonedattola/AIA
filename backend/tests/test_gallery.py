from app.gallery import collect_article_gallery_images, extract_body_images


def test_extract_body_images_dedupes_and_preserves_order():
    html = """
    <p>Test</p>
    <p><img src="/api/uploads/a.jpg" alt="Prima"></p>
    <div class="aia-article-carousel">
      <img src="/api/uploads/b.jpg" alt="Seconda">
      <img src="/api/uploads/a.jpg" alt="Duplicata">
    </div>
    """
    images = extract_body_images(html)
    assert [i["url"] for i in images] == ["/api/uploads/a.jpg", "/api/uploads/b.jpg"]
    assert images[0]["alt"] == "Prima"
    assert images[1]["alt"] == "Seconda"


def test_extract_body_images_empty_html():
    assert extract_body_images("") == []
    assert extract_body_images("<p>Solo testo</p>") == []


def test_collect_article_gallery_images_cover_and_body():
    articles = [
        {
            "id": "a1",
            "title": "Primo articolo",
            "coverUrl": "/api/uploads/cover.jpg",
            "bodyHtml": '<p><img src="/api/uploads/cover.jpg" alt="Duplicata"></p>'
            '<p><img src="/api/uploads/inline.jpg" alt="In pagina"></p>',
        },
        {
            "id": "a2",
            "title": "Secondo",
            "coverUrl": "/api/uploads/other.jpg",
            "bodyHtml": "<p>Solo testo</p>",
        },
    ]
    images = collect_article_gallery_images(articles)
    urls = [i["url"] for i in images]
    assert urls == [
        "/api/uploads/cover.jpg",
        "/api/uploads/inline.jpg",
        "/api/uploads/other.jpg",
    ]
    assert images[0]["caption"] == "Primo articolo"
    assert images[1]["caption"] == "In pagina"
    assert images[2]["source"] == "article_cover"
