# 008 — El transitorio faltante, encontrado y resuelto (dos diseños, comparados)

**Continúa de:** `007-el-llm-no-resuelve-el-transitorio.md`. El diagnóstico de ahí estaba incompleto: no era que el LLM calculara mal la fecha, es que nunca vio el texto del parágrafo transitorio. Se verificó contando ocurrencias literales en el prompt real (`build_prompt()`):

| Cadena | Antes del fix | Después del fix |
|---|---|---|
| `100%` | 1 | 3 |
| `80%` | 0 | 1 |
| `90%` | 0 | 1 |
| `transitorio` | 1 (solo la regla del prompt) | 2 |

**Causa raíz:** `ArticleVersion` no tenía ningún campo para el parágrafo transitorio, y `_load_manual_versions()` no lo leía — aunque ya estaba en `data/manual/ley_2466_2025_art179.json`, bajo `parrafo_transitorio`. El campo `text` del JSON manual, además, nunca incluyó el texto del transitorio (terminaba en el Parágrafo 3°). Es la misma familia de bug que el `\bEXEQUIBLE\b` del parser (docs/experiments/004): la información existe, un paso intermedio la descarta en silencio, y los tests existentes no lo detectaron porque ninguno preguntaba por el tramo.

**El modelo no se había equivocado la primera vez.** Con el 100% como única cifra disponible y la regla del prompt de responder solo con lo que está en el corpus, contestar 100% era lo correcto dado lo que veía. Si hubiera dicho 90% sin tenerlo en el contexto, habría sido peor — una respuesta correcta por la razón equivocada, sacada de conocimiento previo, imposible de auditar.

**El fix, en dos diseños, comparados en vivo:**

- **Diseño A** — incluir el texto literal del parágrafo transitorio en el corpus, sin resolver nada, y dejar que el LLM compare la fecha de hoy contra los tres tramos.
  - Groq (`openai/gpt-oss-120b`): 3/3 aciertos (90%), citando correctamente el tramo y la fecha.
  - Gemini (`gemini-3.1-flash-lite`): acertó en el único intento que no falló por un 503 del servicio (infraestructura, no razonamiento).
- **Diseño B** — resolver el tramo en código (`ArticleVersion.tramo_aplicable(as_of)`) e inyectar el resultado como un hecho ya calculado en el prompt ("Hecho ya resuelto: el tramo mínimo garantizado es 90%..."). Groq lo usó correctamente y además incorporó el matiz legal sin que se le pidiera explícitamente: mencionó que el empleador puede pagar el 100% de forma voluntaria desde ya.

**Por qué se implementaron los dos en vez de solo B:** comparar una fecha contra tres rangos es aritmética determinista — no hay razón de diseño para dejársela a un modelo probabilístico en algo que termina en una nómina, así que B es el diseño de sistema recomendado. Pero A, ya con el texto completo, funcionó de forma consistente en las pruebas — y esa comparación (A vs. B, dos proveedores) es exactamente el tipo de tabla que va a valer la pena tener en el dataset de evaluación de la Fase 1, no solo para el art. 179 sino como patrón general para cualquier artículo con vigencia escalonada.

**Matiz legal para el futuro dataset de evaluación:** el parágrafo transitorio fija un **mínimo garantizado** por tramo, no un tope — el recargo legal es 100% desde el inicio, y el empleador puede pagarlo completo desde ya. Una respuesta esperada que solo acepte la cadena "90%" penalizaría injustamente una respuesta más precisa como "mínimo 90% garantizado, hasta 100% si el empleador lo aplica voluntariamente". El dataset debe reflejar esa nota, no solo el número.

**Resultado final, la pregunta original del art. 179 hoy (2026-09-25):** el generador responde **90%**, citando el art. 179, la Ley 2466 de 2025 y el tramo transitorio aplicable — con `versions[]` + `as_of_date` + el tramo resuelto en código. La diferencia con la Fase 0 (`005-generador-minimo.md`, que respondía 75% con total confianza) es la que este proyecto se propuso demostrar desde el principio.
