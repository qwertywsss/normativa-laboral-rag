# 001 — Scraper + parser del piloto (Capítulo III, arts. 175-186)

**Hipótesis:** el HTML del Gestor Normativo de Función Pública tiene suficiente estructura (headers `<strong>ARTICULO N. TITULO</strong>` + notas `(Modificado por...)` / `(Declarado EXEQUIBLE/INEXEQUIBLE...)`) para extraer, con reglas y regex simples, un registro estructurado por artículo sin necesitar un LLM en esta fase.

**Qué se hizo:**
- Scraper (`src/scraper.py`) descarga el Decreto 2663 de 1950 (texto consolidado del CST) y guarda el HTML crudo con su hash en `data/raw/`.
- Parser (`src/parser.py`) recorre los `<p>`/`<li>` del capítulo III y arma un JSON por artículo: `article_id`, `title`, `text`, `modified_by[]`, `constitutional_review[]`, `status`.
- 7 tests (`tests/test_parser.py`) fijados sobre los casos difíciles conocidos: art. 179 (3 modificaciones en cascada) y art. 182 (inexequibilidad parcial por Sentencia C-710-96).

**Qué falló / sorprendió en el camino:**
- El HTML fuente repite encabezados de página (`<p align="center"><strong>CAPITULO II.</strong></p>`) decenas de veces a lo largo de todo el documento — son artefactos de paginación del documento original, no estructura real. Hubo que filtrarlos explícitamente (`align="center"`) para que no contaminaran el cuerpo de los artículos.
- El primer regex de "Modificado por" asumía siempre la palabra completa "Artículo(s)", pero la fuente alterna entre esa forma y la abreviatura "Art." — y el conector entre el número de artículo y la norma varía ("de la Ley", "del Decreto", "de Ley"). Tuvo que generalizarse.
- El texto de un artículo puede venir en la misma etiqueta `<p>` que su encabezado (ej. art. 176) o en etiquetas separadas (ej. art. 179, con el título solo y el cuerpo en párrafos siguientes). El parser inicial solo cubría el segundo caso y perdía el cuerpo del primero silenciosamente — sin este JSON limpio como base, ningún paso posterior (embeddings, evaluación) hubiera sido confiable.
- Nota de vigencia "(Declarado EXEQUIBLE... Sentencia C-568-93)" aparece pegada a dos artículos distintos (175 y 176) en la fuente. No está claro todavía si es una nota compartida legítima (una sola sentencia que cubre ambos artículos) o un artefacto de la fuente — **pendiente de verificar manualmente contra SUIN-Juriscol antes de confiar en esto para el dataset de evaluación.**

**Qué NO cubre todavía (fuera de alcance de este milestone):**
- Texto histórico completo de versiones anteriores de un artículo (solo se registra *qué* lo modificó, no el texto derogado en sí — eso requeriría cruzar cada norma modificadora en su propia página).
- Jurisprudencia más allá de las notas de vigencia embebidas en el propio texto del CST.

**Resultado:** 13/13 artículos del capítulo extraídos, 7/7 tests pasando. Listo para escalar el mismo parser al CST completo (~500 artículos) como siguiente paso, verificando primero contra un muestreo manual de artículos con historial largo de modificaciones.
