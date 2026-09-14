# 002 — La fuente "oficial consolidada" no está actualizada de forma confiable

**Hallazgo:** el artículo 179 en el snapshot (`data/raw/decreto_2663_1950.html`, capturado 2026-09-13) muestra un recargo del 75% para trabajo dominical y festivo, con `status: "vigente"`. Esa cifra es incorrecta hoy (2026-09-14).

La Ley 2466 de 2025 modificó el artículo 179 con un parágrafo transitorio escalonado:
- 80% desde el 1 de julio de 2025
- 90% desde el 1 de julio de 2026
- 100% desde el 1 de julio de 2027 (plena aplicación)

Hoy la respuesta correcta es **90%**, no 75%.

**Lo más importante de este hallazgo:** no es un bug del parser. El propio HTML fuente está parcialmente actualizado — los artículos 3 y 4 sí traen la marca `(Mod Art 2 de la Ley 2466 de 2025)`, pero el artículo 179 no trae ninguna marca de esa reforma, solo las de la Ley 789/2002 y la Ley 50/1990. Es decir: **la fuente "oficial consolidada" de Función Pública no es internamente consistente sobre qué está o no está vigente.**

**Por qué esto justifica el proyecto:** un RAG que solo recupera texto de esta fuente y lo presenta como vigente va a responder con confianza un dato incorrecto, sin ninguna señal de alerta — ni el retrieval ni el LLM tienen forma de saber que la fuente está desactualizada en ese punto específico. Resolver esto (cruzando al menos una segunda fuente para afectaciones, y modelando explícitamente `vigente_desde`/`vigente_hasta` por versión en vez de un único `status` estático) es el problema central que este proyecto intenta demostrar que sabe manejar, no un efecto secundario.

**Siguiente paso:** cruzar el artículo 179 contra una segunda fuente (SUIN-Juriscol, o la Ley 2466 de 2025 directamente en el Gestor Normativo) para confirmar la redacción vigente y las fechas exactas del escalonamiento, antes de rediseñar el esquema de versiones.
