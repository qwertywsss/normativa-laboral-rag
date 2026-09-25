import json
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from src.versions import get_article

load_dotenv()

CORPUS_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "capitulo_iii_trabajo_dominical.json"
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "generador_v2.md"


def _pilot_article_ids() -> list[str]:
    return [a["article_id"] for a in json.loads(CORPUS_PATH.read_text(encoding="utf-8"))]


def load_corpus_text(as_of: date) -> str:
    lines = []
    for article_id in _pilot_article_ids():
        art = get_article(article_id, as_of)
        texto = art.text
        if art.texto_transitorio:
            texto = f"{texto} {art.texto_transitorio}"
        tramo = art.tramo_aplicable(as_of)
        if tramo:
            # Resuelto en código, no dejado al LLM: comparar una fecha contra
            # tres rangos es aritmética determinista (ver docs/experiments/007).
            texto += (
                f" [Hecho ya resuelto para la fecha de hoy: el tramo mínimo garantizado "
                f"es {tramo.valor} (vigente desde {tramo.vigente_desde.isoformat()}); el "
                f"empleador puede pagar hasta el 100% desde ya, de forma voluntaria, "
                f"según el propio parágrafo transitorio.]"
            )
        lines.append(f"Artículo {art.article_id} ({art.title}) — {art.fuente}: {texto}")
    return "\n\n".join(lines)


def build_prompt(pregunta: str, as_of: date) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.format(corpus=load_corpus_text(as_of), pregunta=pregunta, as_of_date=as_of.isoformat())


def generate_gemini(prompt: str) -> str:
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    # "gemini-flash-latest" resolvió a un modelo con demanda alta y 503
    # constantes en las pruebas; se fija una versión estable disponible.
    response = client.models.generate_content(model="gemini-3.1-flash-lite", contents=prompt)
    return response.text.strip()


def generate_groq(prompt: str) -> str:
    from groq import Groq

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


PROVIDERS = {"gemini": generate_gemini, "groq": generate_groq}


def answer(pregunta: str, provider: str = "gemini", as_of: date | None = None) -> str:
    as_of = as_of or date.today()
    prompt = build_prompt(pregunta, as_of)
    return PROVIDERS[provider](prompt)


if __name__ == "__main__":
    pregunta = sys.argv[1] if len(sys.argv) > 1 else "¿Cuál es el recargo por trabajo en domingo y festivos?"
    provider = sys.argv[2] if len(sys.argv) > 2 else "gemini"
    as_of = date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else date.today()
    print(f"[{provider} | as_of={as_of}] {pregunta}\n")
    print(answer(pregunta, provider, as_of))
