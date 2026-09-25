from datetime import date

import pytest

from src.versions import get_article, load_versions


def test_article_179_has_two_versions():
    versions = load_versions("179")
    assert len(versions) == 2
    assert versions[0].vigente_hasta == date(2025, 6, 30)
    assert versions[1].vigente_desde == date(2025, 7, 1)
    assert versions[1].vigente_hasta is None


def test_get_article_before_reform_returns_cst_version():
    art = get_article("179", date(2024, 1, 1))
    assert art.fuente.startswith("Decreto 2663 de 1950")
    assert "setenta y cinco por ciento" in art.text


def test_get_article_after_reform_returns_ley_2466_version():
    art = get_article("179", date(2026, 9, 25))
    assert art.fuente == "Ley 2466 de 2025"
    assert "recargo del ciento por ciento (100%)" in art.text


def test_get_article_exactly_on_transition_date():
    art = get_article("179", date(2025, 7, 1))
    assert art.fuente == "Ley 2466 de 2025"

    art_day_before = get_article("179", date(2025, 6, 30))
    assert art_day_before.fuente.startswith("Decreto 2663")


def test_article_without_manual_version_has_a_single_open_ended_version():
    versions = load_versions("176")
    assert len(versions) == 1
    assert versions[0].vigente_hasta is None
    assert get_article("176", date(2026, 9, 25)).article_id == "176"


def test_unknown_article_id_raises():
    with pytest.raises(ValueError):
        load_versions("999999")
