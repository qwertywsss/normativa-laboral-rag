from pathlib import Path

import pytest

from src.parser import parse_chapter

HTML_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "decreto_2663_1950.html"


@pytest.fixture(scope="module")
def articles():
    return {
        a.article_id: a
        for a in parse_chapter(
            HTML_PATH, "Capítulo III - Trabajo Dominical y Festivo", ("175", "186")
        )
    }


def test_extracts_all_articles_in_range(articles):
    expected_ids = {"175", "176", "177", "178", "179", "180", "181", "182", "183", "184", "185", "185A", "186"}
    assert expected_ids.issubset(articles.keys())


def test_article_179_has_title_and_body(articles):
    art = articles["179"]
    assert art.title == "TRABAJO DOMINICAL Y FESTIVO"
    assert "setenta y cinco por ciento" in art.text
    assert "PARÁGRAFO" not in art.text[:50]


def test_article_179_captures_all_historical_modifications(articles):
    art = articles["179"]
    laws = {(m.type, m.number, m.year) for m in art.modified_by}
    assert ("ley", "789", 2002) in laws
    assert ("ley", "50", 1990) in laws
    assert ("decreto", "2351", 1965) in laws
    assert len(art.modified_by) == 3


def test_article_179_modification_notes_excluded_from_body_text(articles):
    art = articles["179"]
    assert "Modificado por" not in art.text


def test_article_182_flagged_by_constitutional_court(articles):
    art = articles["182"]
    assert len(art.constitutional_review) == 1
    review = art.constitutional_review[0]
    assert review.sentencia == "C-710-96"
    assert art.status == "modificado_por_sentencia"


def test_article_with_no_modifications_stays_vigente(articles):
    art = articles["176"]
    assert art.modified_by == []
    assert art.status == "vigente"


def test_snapshot_hash_is_recorded(articles):
    art = articles["179"]
    assert len(art.raw_snapshot_sha256) == 64


def test_handles_articulo_header_with_accent(tmp_path):
    html = (
        "<p><strong>ARTICULO 500. UNO.</strong> Texto cero.</p>"
        "<p><strong>ARTÍCULO 501. DOS.</strong> Texto uno.</p>"
        "<p><strong>ARTICULO 502. TRES.</strong> Texto dos.</p>"
    )
    path = tmp_path / "mini.html"
    path.write_text(html, encoding="utf-8")

    arts = {a.article_id: a for a in parse_chapter(path, "Test", ("500", "502"))}

    assert "501" in arts
    assert arts["501"].title == "DOS"
