import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

CORPUS_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "capitulo_iii_trabajo_dominical.json"
MANUAL_DIR = Path(__file__).resolve().parent.parent / "data" / "manual"

# El CST original (Decreto 2663 de 1950) no tiene una fecha de inicio que nos
# importe rastrear aquí; sirve como "desde siempre" para cualquier artículo
# que no tenga una versión manual posterior.
EARLIEST_DATE = date(1950, 1, 1)


@dataclass
class ArticleVersion:
    article_id: str
    title: str
    text: str
    fuente: str
    vigente_desde: date
    vigente_hasta: date | None


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _load_manual_versions(article_id: str) -> list[ArticleVersion]:
    versions = []
    for path in sorted(MANUAL_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("article_id") != article_id:
            continue
        mod = data["modified_by"]
        fuente = f"{mod['type'].replace('_', ' ').title()} {mod['number']} de {mod['year']}"
        versions.append(
            ArticleVersion(
                article_id=article_id,
                title=data["title"],
                text=data["text"],
                fuente=fuente,
                vigente_desde=_parse_date(data["vigente_desde"]),
                vigente_hasta=_parse_date(data.get("vigente_hasta")),
            )
        )
    return versions


def load_versions(article_id: str) -> list[ArticleVersion]:
    corpus = {a["article_id"]: a for a in json.loads(CORPUS_PATH.read_text(encoding="utf-8"))}
    base = corpus.get(article_id)
    if base is None:
        raise ValueError(f"Artículo {article_id} no está en el corpus del piloto")

    manual = sorted(_load_manual_versions(article_id), key=lambda v: v.vigente_desde)
    base_hasta = manual[0].vigente_desde - timedelta(days=1) if manual else None

    base_version = ArticleVersion(
        article_id=article_id,
        title=base["title"],
        text=base["text"],
        fuente="Decreto 2663 de 1950 (texto consolidado, Gestor Normativo)",
        vigente_desde=EARLIEST_DATE,
        vigente_hasta=base_hasta,
    )
    return [base_version, *manual]


def get_article(article_id: str, as_of: date) -> ArticleVersion:
    for version in load_versions(article_id):
        if version.vigente_desde <= as_of and (version.vigente_hasta is None or as_of <= version.vigente_hasta):
            return version
    raise ValueError(f"No hay versión vigente del artículo {article_id} para la fecha {as_of}")
