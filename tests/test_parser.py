import re
from pathlib import Path

import pytest

from src.parser import ModifiedBy, filter_range, parse_all_articles, parse_chapter

HTML_PATH = Path(__file__).resolve().parent / "fixtures" / "capitulo_iii_trabajo_dominical.html"


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
    # No se fija la cifra del recargo (75% en el snapshot actual): ya sabemos
    # que está desactualizada (ver docs/experiments/002-fuente-desactualizada.md)
    # y cambiará con cada reforma. Se verifica la estructura, no el valor.
    assert re.search(r"recargo del \w[\w\s]* por ciento", art.text)
    assert "PARÁGRAFO" not in art.text[:50]


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Fuente desactualizada (ver docs/experiments/002-fuente-desactualizada.md): "
        "Función Pública aún no marca la reforma de la Ley 2466 de 2025 en el art. 179. "
        "Si esto empieza a pasar, la fuente ya se actualizó (o cruzamos una segunda "
        "fuente) y hay que quitar este xfail."
    ),
)
def test_article_179_freshness_reflects_ley_2466_de_2025(articles):
    art = articles["179"]
    laws = {(m.type, m.number, m.year) for m in art.modified_by}
    assert ("ley", "2466", 2025) in laws


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


def test_article_185a_captures_adicionado_por(articles):
    art = articles["185A"]
    assert len(art.modified_by) == 1
    assert art.modified_by[0].type == "ley"
    assert art.modified_by[0].number == "50"
    assert art.modified_by[0].year == 1990


def test_handles_hyphenated_article_id(tmp_path):
    # ARTICULO 391-1 (adicionado con guion, no con letra como 185A) se perdía
    # por completo: el regex no matcheaba en absoluto y el artículo desaparecía
    # sin ningún aviso.
    html = (
        "<p><strong>ARTICULO 391. UNO.</strong> Texto original.</p>"
        "<p><strong>ARTICULO 391-1. DIRECTIVAS SECCIONALES.</strong> Texto nuevo.</p>"
        "<p><strong>ARTICULO 392. TRES.</strong> Otro texto.</p>"
    )
    path = tmp_path / "mini.html"
    path.write_text(html, encoding="utf-8")

    arts = {a.article_id: a for a in parse_chapter(path, "Test", ("391", "392"))}

    assert "391-1" in arts
    assert arts["391-1"].title == "DIRECTIVAS SECCIONALES"


def test_recognizes_abbreviated_mod_form(tmp_path):
    html = "<p><strong>ARTICULO 500. UNO.</strong> Texto.</p><p>(Mod Art 2 de la Ley 2466 de 2025)</p>"
    path = tmp_path / "mini.html"
    path.write_text(html, encoding="utf-8")

    arts = {a.article_id: a for a in parse_chapter(path, "Test", ("500", "500"))}

    mods = arts["500"].modified_by
    assert len(mods) == 1
    assert mods[0] == ModifiedBy(type="ley", number="2466", year=2025, source_articles="2")


def test_derogado_por_articulo_marks_status(tmp_path):
    html = "<p><strong>ARTICULO 501. UNO.</strong> Texto.</p><p>(Derogado por el Art. 9 de la Ley 11 de 1984)</p>"
    path = tmp_path / "mini.html"
    path.write_text(html, encoding="utf-8")

    arts = {a.article_id: a for a in parse_chapter(path, "Test", ("501", "501"))}

    assert arts["501"].status == "derogado"
    assert arts["501"].modified_by[0].number == "11"


def test_derogado_por_norma_completa_sin_articulo(tmp_path):
    html = "<p><strong>ARTICULO 502. UNO.</strong> Texto.</p><p>(Derogado la Ley 100 de 1993)</p>"
    path = tmp_path / "mini.html"
    path.write_text(html, encoding="utf-8")

    arts = {a.article_id: a for a in parse_chapter(path, "Test", ("502", "502"))}

    art = arts["502"]
    assert art.status == "derogado"
    assert art.modified_by == [ModifiedBy(type="ley", number="100", year=1993)]


def test_range_stops_when_last_article_has_no_body_paragraphs(tmp_path):
    # Bug real: si el filtrado se hacía en el mismo recorrido que el parseo, el
    # corte de rango dependía de procesar un párrafo de CUERPO del último
    # artículo. Un artículo final sin cuerpo propio (título en el mismo <p> que
    # el encabezado, sin párrafos después) nunca disparaba el corte y el
    # parseo seguía de largo hasta el final del documento.
    html = (
        "<p><strong>ARTICULO 600. UNO.</strong> Texto seiscientos.</p>"
        "<p><strong>ARTICULO 601. DOS.</strong></p>"
        "<p><strong>ARTICULO 602. TRES.</strong> No debería aparecer.</p>"
    )
    path = tmp_path / "mini.html"
    path.write_text(html, encoding="utf-8")

    arts = parse_chapter(path, "Test", ("600", "601"))

    assert [a.article_id for a in arts] == ["600", "601"]


def test_filter_range_raises_when_start_id_missing(tmp_path):
    html = "<p><strong>ARTICULO 1. UNO.</strong> Texto.</p>"
    path = tmp_path / "mini.html"
    path.write_text(html, encoding="utf-8")

    all_articles = parse_all_articles(path, "Test")
    with pytest.raises(ValueError):
        filter_range(all_articles, "999", "999")


def test_normalizes_ordinal_suffix_and_uppercases_real_letter(tmp_path):
    html = (
        "<p><strong>ARTICULO 5o. DEFINICION.</strong> Texto cinco.</p>"
        "<p><strong>ARTICULO 6º. OTRO.</strong> Texto seis.</p>"
        "<p><strong>ARTICULO 241a. CON LETRA REAL.</strong> Texto con letra.</p>"
    )
    path = tmp_path / "mini.html"
    path.write_text(html, encoding="utf-8")

    arts = {a.article_id: a for a in parse_chapter(path, "Test", ("5", "241A"))}

    assert "5" in arts
    assert "6" in arts
    assert "241A" in arts
    assert "5o" not in arts
    assert "241a" not in arts


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
