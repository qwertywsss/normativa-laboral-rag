import hashlib
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup

ARTICLE_HEADER_RE = re.compile(r"^ARTICULO\s+(\d+[A-Z]?)\.\s*(.*)$", re.IGNORECASE)
MODIFIED_BY_RE = re.compile(
    r"Modificado por (?:el|los)?\s*(?:Art\.|Art[íi]culos?)\s+"
    r"(?P<source_articles>[\d\wáéíóú° y,]+?)\s+"
    r"(?:del|de la|de el|de)\s+(?P<type>Decreto|Ley)\s+(?P<number>\d+)\s+de\s+(?P<year>\d{4})",
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
    source_articles: str


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


def _classify_paragraph(paragraph_text: str, article: Article) -> bool:
    """Returns True if the paragraph was a metadata note (not article body)."""
    mod_match = MODIFIED_BY_RE.search(paragraph_text)
    if mod_match:
        article.modified_by.append(
            ModifiedBy(
                type=mod_match.group("type").lower(),
                number=mod_match.group("number"),
                year=int(mod_match.group("year")),
                source_articles=_clean(mod_match.group("source_articles")),
            )
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


def parse_chapter(html_path: Path, chapter: str, article_range: tuple[str, str]) -> list[Article]:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    snapshot_hash = hashlib.sha256(html_path.read_bytes()).hexdigest()

    start_id, end_id = article_range
    in_range = False
    past_end = False
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
            article_id = header_match.group(1)
            if past_end:
                break
            if article_id == start_id:
                in_range = True
            if in_range:
                if current:
                    articles.append(current)
                current = Article(
                    article_id=article_id,
                    code="CST",
                    chapter=chapter,
                    title=_clean(header_match.group(2)).rstrip("."),
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

        if current.article_id == end_id:
            past_end = True

    if current and current not in articles:
        articles.append(current)

    return articles


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
