import hashlib
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup

ARTICLE_HEADER_RE = re.compile(r"^ART[IÍ]CULO\s+(\d+(?:-\d+)?)\s*([A-Za-zº°]?)\.\s*(.*)$", re.IGNORECASE)
ORDINAL_SUFFIXES = {"o", "º", "°"}
# Nota de afectación que cita el artículo puntual de la norma que la origina, ej.:
# "Modificado por el Art. 26 de la Ley 789 de 2002", "Mod Art 2 de la Ley 2466 de 2025",
# "Derogado por el numeral 4 del Art. 3 de la Ley 48 de 1968".
MODIFIED_BY_RE = re.compile(
    r"(?:Numeral\s+\d+\s*,?\s*)?"
    r"\b(?P<verb>Modificad[oa]|Mod|Derogad[oa]|Subrogad[oa]|Adicionad[oa])\b\s*"
    r"(?:por)?\s*(?:el|los|la)?\s*"
    r"(?:numeral\s+\d+\s*,?\s*(?:del|de)?\s*)?"
    r"(?:Art\.?|Art[íi]culos?\.?)\s*"
    r"(?P<source_articles>[\d\wáéíóú° y,]+?)\s+"
    r"(?:del|de la|de el|de)\s+(?P<type>Decreto\s+Ley|Decreto|Ley)\s+(?P<number>\d+)\s+de\s+(?P<year>\d{4})",
    re.IGNORECASE,
)

# Afectación directa por una norma completa, sin citar un artículo puntual, ej.:
# "Derogado la Ley 100 de 1993", "Subrogado por La ley 100 de 1993".
DIRECT_NORM_RE = re.compile(
    r"\b(?P<verb>Derogad[oa]|Subrogad[oa])\b\s*(?:por)?\s*(?:el|los|la)?\s*"
    r"(?P<type>Decreto\s+Ley|Decreto|Ley)\s+(?P<number>\d+)\s+de\s+(?P<year>\d{4})",
    re.IGNORECASE,
)
CONSTITUTIONAL_REVIEW_RE = re.compile(
    r"Declarad[oa]s?\s+(?P<result>EXEQUIBLE|INEXEQUIBLE)[^)]*Sentencia\s*(?P<sentencia>[A-Z]-\d+-\d+)",
    re.IGNORECASE,
)

SOURCE_URL = "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=199983"


@dataclass
class ModifiedBy:
    type: str
    number: str
    year: int
    source_articles: str = ""


@dataclass
class ConstitutionalReview:
    sentencia: str
    result: str
    raw_note: str


@dataclass
class Article:
    article_id: str
    code: str
    chapter: str
    title: str
    text: str
    modified_by: list = field(default_factory=list)
    constitutional_review: list = field(default_factory=list)
    status: str = "vigente"
    source_url: str = SOURCE_URL
    raw_snapshot_path: str = "data/raw/decreto_2663_1950.html"
    raw_snapshot_sha256: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_article_id(digits: str, suffix: str) -> str:
    # "5o.", "5º." son formas antiguas de escribir el ordinal "5.", no una letra
    # que distinga un artículo distinto (a diferencia de "185A", sí real).
    if not suffix or suffix.lower() in ORDINAL_SUFFIXES:
        return digits
    return f"{digits}{suffix.upper()}"


def _register_affectation(article: Article, verb: str, type_: str, number: str, year: str, source_articles: str = "") -> None:
    article.modified_by.append(
        ModifiedBy(
            type=type_.lower().replace(" ", "_"),
            number=number,
            year=int(year),
            source_articles=source_articles,
        )
    )
    if verb.lower().startswith("derog"):
        article.status = "derogado"


def _classify_paragraph(paragraph_text: str, article: Article) -> bool:
    """Returns True if the paragraph was a metadata note (not article body)."""
    mod_match = MODIFIED_BY_RE.search(paragraph_text)
    if mod_match:
        _register_affectation(
            article,
            verb=mod_match.group("verb"),
            type_=mod_match.group("type"),
            number=mod_match.group("number"),
            year=mod_match.group("year"),
            source_articles=_clean(mod_match.group("source_articles")),
        )
        return True

    direct_match = DIRECT_NORM_RE.search(paragraph_text)
    if direct_match:
        _register_affectation(
            article,
            verb=direct_match.group("verb"),
            type_=direct_match.group("type"),
            number=direct_match.group("number"),
            year=direct_match.group("year"),
        )
        return True

    review_match = CONSTITUTIONAL_REVIEW_RE.search(paragraph_text)
    if review_match:
        upper_text = paragraph_text.upper()
        is_inexequible = "INEXEQUIBLE" in upper_text
        article.constitutional_review.append(
            ConstitutionalReview(
                sentencia=review_match.group("sentencia").upper(),
                result="exequible_parcial" if (is_inexequible and "EXEQUIBLE" in upper_text) else review_match.group("result").lower(),
                raw_note=_clean(paragraph_text),
            )
        )
        if is_inexequible:
            article.status = "modificado_por_sentencia" if "salvo" in paragraph_text.lower() else "inexequible"
        return True

    return False


def parse_all_articles(html_path: Path, chapter: str) -> list[Article]:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    snapshot_hash = hashlib.sha256(html_path.read_bytes()).hexdigest()

    articles: list[Article] = []
    current: Article | None = None

    for p in soup.find_all(["p", "li"]):
        # Los <p align="center"> son encabezados de página repetidos en cada
        # "hoja" del documento original (CAPITULO II/III, títulos de sección);
        # no pertenecen al cuerpo de ningún artículo.
        if p.name == "p" and p.get("align") == "center":
            continue

        strong = p.find("strong") if p.name == "p" else None
        header_match = ARTICLE_HEADER_RE.match(_clean(strong.get_text())) if strong else None

        if header_match:
            if current:
                articles.append(current)
            current = Article(
                article_id=_normalize_article_id(header_match.group(1), header_match.group(2)),
                code="CST",
                chapter=chapter,
                title=_clean(header_match.group(3)).rstrip("."),
                text="",
                raw_snapshot_sha256=snapshot_hash,
            )
            full_text = _clean(p.get_text())
            title_text = _clean(strong.get_text())
            inline_body = full_text[len(title_text):].strip() if full_text.startswith(title_text) else ""
            if inline_body and not _classify_paragraph(inline_body, current):
                current.text = inline_body
            continue

        if current is None:
            continue

        text = _clean(p.get_text())
        if not text:
            continue

        if not _classify_paragraph(text, current):
            current.text = f"{current.text} {text}".strip() if current.text else text

    if current:
        articles.append(current)

    return articles


def filter_range(articles: list[Article], start_id: str, end_id: str) -> list[Article]:
    ids = [a.article_id for a in articles]
    try:
        start_idx = ids.index(start_id)
    except ValueError:
        raise ValueError(f"No se encontró el artículo de inicio '{start_id}'") from None
    try:
        end_idx = ids.index(end_id, start_idx)
    except ValueError:
        raise ValueError(f"No se encontró el artículo de fin '{end_id}' después de '{start_id}'") from None
    return articles[start_idx : end_idx + 1]


def parse_chapter(html_path: Path, chapter: str, article_range: tuple[str, str]) -> list[Article]:
    start_id, end_id = article_range
    return filter_range(parse_all_articles(html_path, chapter), start_id, end_id)


if __name__ == "__main__":
    import json

    html_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "decreto_2663_1950.html"
    out_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "capitulo_iii_trabajo_dominical.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    arts = parse_chapter(html_path, "Capítulo III - Trabajo Dominical y Festivo", ("175", "186"))
    out_path.write_text(
        json.dumps([a.to_dict() for a in arts], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"{len(arts)} artículos escritos en {out_path}")
