# 005 — Generador mínimo: responde con confianza el dato desactualizado

**Qué se construyó:** un generador sin recuperación ni fecha de corte (`src/generator.py`). Los 13 artículos del piloto (Cap. III) van completos como contexto en el prompt (`prompts/generador_v1.md`), versionado en archivo. El prompt exige citar el artículo y abstenerse si la pregunta no está cubierta por el corpus. Soporta dos proveedores intercambiables (Gemini Flash y Groq), ambos con capa gratuita.

**Resultado, pregunta:** "¿Cuál es el recargo por trabajo en domingo y festivos?"

- **Gemini** (`gemini-flash-latest`): _"Según el artículo 179, el trabajo en domingo y festivos se remunerará con un recargo del setenta y cinco por ciento (75%) sobre el salario ordinario..."_
- **Groq** (`openai/gpt-oss-120b`): _"El recargo... es del setenta y cinco por ciento (75%)... según lo establece el artículo 179..."_

Ambos proveedores citan correctamente el artículo 179, y ambos responden **75%** con total confianza — sin ninguna señal de duda, sin mencionar que existe una reforma posterior. Es exactamente el dato que sabíamos desactualizado desde `docs/experiments/002-fuente-desactualizada.md`: hoy (2026-09) la cifra vigente es 90% por el escalonamiento transitorio de la Ley 2466 de 2025.

**Por qué esto es el punto de partida, no un bug:** el generador está haciendo exactamente lo que se le pidió — citar fielmente lo que dice el corpus que se le dio. El problema no es el LLM ni el prompt: es que el corpus es una foto fija de un momento, y aquí no hay ningún mecanismo que sepa que esa foto envejeció. Sin `versions[]` ni `as_of_date`, no hay forma de que el sistema se dé cuenta.

**El guardrail de abstención sí funciona:** ante "Mi jefe me trata mal, ¿qué hago?" (categoría "fuera de alcance" del dataset de evaluación planeado), el generador responde _"No tengo información suficiente en el corpus para responder esto"_ en vez de inventar asesoría legal. Esto confirma que la regla del prompt (punto 3) se sostiene incluso sin necesidad todavía de guardrails de código.

**Siguiente paso:** cargar el texto real de la Ley 2466 de 2025 para el art. 179 (segunda fuente, `docs/experiments/006`) — ahí por primera vez habrá dos versiones reales con texto de un mismo artículo, que es lo mínimo que necesita `versions[]` para dejar de ser un contenedor vacío.
