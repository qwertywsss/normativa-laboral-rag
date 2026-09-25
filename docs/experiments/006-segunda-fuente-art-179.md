# 006 — Segunda fuente para el art. 179: la Ley 2466 de 2025

**Qué se hizo:** se descargó y guardó (con hash) el texto oficial de la Ley 2466 de 2025 desde el Gestor Normativo de Función Pública, y se extrajo programáticamente (con BeautifulSoup, no a mano tecleado) el texto exacto del Artículo 14 de esa ley, que reforma el artículo 179 del CST. Queda en `data/manual/ley_2466_2025_art179.json`.

**Por qué "manual" y no scraper genérico:** a diferencia del CST (un documento consolidado con estructura repetible para ~500 artículos), esta es una norma puntual que solo nos interesa por un artículo específico. No se justifica un scraper genérico para un caso de uso; se hizo la extracción una vez, con el mismo cuidado de reproducibilidad (snapshot + hash) que el resto del proyecto.

**El hallazgo que esto habilita:** ahora hay, por primera vez, **dos versiones reales con texto** del mismo artículo:

1. La del CST consolidado (`data/processed/capitulo_iii_trabajo_dominical.json`): recargo del 75%, título "TRABAJO DOMINICAL Y FESTIVO".
2. La de la Ley 2466 de 2025 (`data/manual/ley_2466_2025_art179.json`): recargo escalonado 80→90→100% según fecha, título cambiado a "Remuneración en días de descanso obligatorio" (el nombre del concepto "dominical" queda reemplazado por "día de descanso obligatorio" en todo el artículo, según su propio Parágrafo 2°).

**El detalle que hace esto interesante de verdad:** la Ley 2466 no fija un solo valor nuevo — fija un **parágrafo transitorio** con tres tramos de vigencia (80% desde 2025-07-01, 90% desde 2026-07-01, 100% desde 2027-07-01). Eso significa que la "versión 2025" del artículo no tiene una única respuesta correcta: la respuesta depende de la fecha de la consulta. Sin un parámetro `as_of_date`, ni siquiera tener el texto correcto alcanza — hace falta saber *cuándo* se pregunta.

**Siguiente paso:** con estas dos versiones reales ya disponibles, `versions[]` deja de ser un contenedor vacío. Toca diseñar `get_article(id, as_of)` que, dada una fecha, devuelva el texto y la cifra correcta — y volver a correr el generador para confirmar que pasa de responder 75% a responder 90% (la cifra vigente hoy, 2026-09-25).
