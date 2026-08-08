import io

import pytest
from PIL import Image

from app.gallery_curation import (
    _analyze_bytes,
    _detect_aspect,
    _hamming,
    _should_skip_url,
    build_dedup_state_from_existing,
    process_gallery_image,
    select_curated_candidates,
)


def _jpeg(w: int, h: int, color=(120, 80, 40)) -> bytes:
    img = Image.new("RGB", (w, h), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def test_should_skip_url_patterns():
    assert _should_skip_url("/favicon.ico")
    assert _should_skip_url("https://x.com/logo.png")
    assert not _should_skip_url("/api/uploads/photo.jpg")


def test_analyze_bytes_rejects_small_image():
    assert _analyze_bytes(_jpeg(200, 200), is_cover=False) is None


def test_analyze_bytes_accepts_quality_photo():
    data = _jpeg(1200, 800)
    analysis = _analyze_bytes(data, is_cover=True)
    assert analysis is not None
    assert analysis.aspect == "16:9"
    assert analysis.quality_score > 50


def test_detect_aspect_portrait():
    assert _detect_aspect(600, 900) == "9:16"
    assert _detect_aspect(900, 600) == "16:9"


def test_process_gallery_image_exports_jpeg():
    data = _jpeg(1600, 900)
    out, aspect = process_gallery_image(data, "16:9")
    assert aspect == "16:9"
    img = Image.open(io.BytesIO(out))
    w, h = img.size
    assert abs((w / h) - (16 / 9)) < 0.05


def test_hamming_identical_hashes():
    # soglia qualità richiede immagini abbastanza grandi (non solo dimensioni minime)
    data = _jpeg(1200, 800)
    a = _analyze_bytes(data, is_cover=False)
    b = _analyze_bytes(data, is_cover=False)
    assert a and b
    assert _hamming(a.phash, b.phash) == 0


@pytest.mark.asyncio
async def test_select_curated_candidates_dedupes_similar():
    state = build_dedup_state_from_existing([])
    candidates = [
        {
            "url": "/api/uploads/a.jpg",
            "caption": "A",
            "articleId": "art1",
            "source": "article_cover",
            "category": "",
            "photoDate": "2026-01-01",
        },
        {
            "url": "/api/uploads/b.jpg",
            "caption": "B",
            "articleId": "art1",
            "source": "article_body",
            "category": "",
            "photoDate": "2026-01-01",
        },
    ]

    async def fake_analyze(candidate):
        from app.gallery_curation import CuratedCandidate, ImageAnalysis

        if candidate["url"].endswith("a.jpg"):
            data = _jpeg(1200, 800, (10, 10, 10))
        else:
            data = _jpeg(1200, 800, (12, 12, 12))
        analysis = _analyze_bytes(data, is_cover=candidate["source"] == "article_cover")
        assert analysis
        return CuratedCandidate(candidate=candidate, analysis=analysis)

    from app import gallery_curation

    original = gallery_curation.analyze_candidate
    gallery_curation.analyze_candidate = fake_analyze
    try:
        selected = await select_curated_candidates(candidates, state, max_total=5)
    finally:
        gallery_curation.analyze_candidate = original

    assert len(selected) == 1
