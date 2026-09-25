import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

CORPUS_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "capitulo_iii_trabajo_dominical.json"
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "generador_v1.md"


def load_corpus_text() -> str:
    articles = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    return "\n\n".join(
        f"Artículo {a['article_id']} ({a['title']}): {a['text']}" for a in articles
    )


def build_prompt(pregunta: str) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.format(corpus=load_corpus_text(), pregunta=pregunta)


def generate_gemini(prompt: str) -> str:
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(model="gemini-flash-latest", contents=prompt)
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


def answer(pregunta: str, provider: str = "gemini") -> str:
    prompt = build_prompt(pregunta)
    return PROVIDERS[provider](prompt)


if __name__ == "__main__":
    pregunta = sys.argv[1] if len(sys.argv) > 1 else "¿Cuál es el recargo por trabajo en domingo y festivos?"
    provider = sys.argv[2] if len(sys.argv) > 2 else "gemini"
    print(f"[{provider}] {pregunta}\n")
    print(answer(pregunta, provider))
