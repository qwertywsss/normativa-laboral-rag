# 007 — Darle al LLM el texto correcto no basta: no resuelve el tramo transitorio

**Hipótesis que se estaba probando:** con `get_article(id, as_of)` devolviendo la versión correcta (Ley 2466 de 2025) y la fecha de hoy explícita en el prompt, el generador pasaría de responder 75% a responder 90% para el art. 179, dejando que el LLM calcule qué tramo del parágrafo transitorio aplica.

**Resultado real, pregunta "¿Cuál es el recargo por trabajo en domingo y festivos?", `as_of=2026-09-25`:**

- **Gemini** (`gemini-flash-latest`): no se pudo probar de forma consistente por errores 503 transitorios del servicio en el momento de la prueba.
- **Groq** (`openai/gpt-oss-120b`): responde **100%**, y afirma explícitamente _"No existen tramos o variaciones por fecha; el porcentaje es único"_ — una afirmación falsa: el mismo texto que se le pasó en el contexto contiene el parágrafo transitorio con los tres tramos (80% desde 2025-07-01, 90% desde 2026-07-01, 100% desde 2027-07-01).

**Por qué pasa esto:** el modelo tiene el numeral 1 del artículo ("recargo del ciento por ciento (100%)...") como la regla aparentemente principal, y el parágrafo transitorio como una excepción temporal más abajo en el texto. Resolver correctamente cuál de los tres tramos aplica exige comparar la fecha de hoy contra tres rangos de fechas en prosa — una tarea de razonamiento aritmético-temporal que, sobre este texto y con estos modelos económicos (Flash / OSS de Groq, elegidos por ser gratuitos), no se resuelve de forma confiable con solo "dale la fecha y pídele que calcule".

**La lección, y por qué es la buena:** confirma exactamente la tesis del proyecto (`docs/experiments/002`, `004`) llevada un paso más allá. No basta con que `versions[]` le dé al sistema el texto vigente correcto — si la vigencia dentro de ese texto depende de aritmética de fechas, dejársela al LLM en lenguaje natural es frágil. Esto es precisamente el tipo de caso "vigencia" que el dataset de evaluación de la Fase 1 necesita cubrir, y aquí tenemos el primer caso real, ya fallando, antes incluso de construir el dataset.

**Siguiente paso propuesto (no ejecutado todavía, a la espera de confirmación):** resolver el tramo transitorio en código — ya existe la estructura `parrafo_transitorio.escalonamiento` en `data/manual/ley_2466_2025_art179.json` con las fechas exactas — y pasarle al LLM el porcentaje ya resuelto como un hecho explícito en el prompt (ej. "Nota: para la fecha indicada, el recargo aplicable según el escalonamiento es 90%"), en vez de pedirle que haga la aritmética de fechas él mismo. Esto no le quita citación al LLM (sigue explicando y citando el artículo), pero saca el cálculo de fechas —que sí se puede verificar con un test— del lado no determinista.
