# normativa-laboral-rag

Sistema de preguntas y respuestas sobre el Código Sustantivo del Trabajo (CST) de Colombia, con énfasis en la evaluación del pipeline (no solo en construirlo).

## Por qué este dominio

El CST lleva 75 años modificándose por capas (Decreto 2351/1965, Ley 50/1990, Ley 789/2002, Ley 2466/2025, entre otras). Un mismo artículo puede tener varias redacciones vigentes en distintas fechas, y el conocimiento paramétrico de un LLM suele estar desactualizado frente a la última reforma. Esto convierte la vigencia temporal en un problema de ingeniería real, no solo de recuperación de texto.

Además, el ID de artículo es un ground truth verificable: se puede medir con exactitud si el sistema citó el artículo correcto (precisión de citación, recall@k), sin depender solo de LLM-as-judge.

## Estado actual

Piloto sobre el **Capítulo III — Trabajo Dominical y Festivo** (arts. 175-186), elegido porque ya contiene los casos difíciles que debe resolver el parser: un artículo con múltiples modificaciones históricas (art. 179) y un artículo declarado parcialmente inexequible por la Corte Constitucional (art. 182).

## Fuentes

- [Gestor Normativo — Función Pública](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=199983) (Decreto 2663 de 1950, texto consolidado del CST)
- [SUIN-Juriscol](https://www.suin-juriscol.gov.co/) — Ministerio de Justicia

El HTML crudo de cada fuente se guarda en `data/raw/` (con su hash) para que los resultados sean reproducibles aunque la fuente cambie.

### Nota sobre TLS

`funcionpublica.gov.co` sirve un certificado intermedio equivocado (el de "Domain Validation" en vez del de "Organization Validation" que realmente firmó su certificado), por lo que la cadena TLS nunca cierra con los certificados raíz estándar. El scraper no desactiva la verificación TLS (`verify=False` sería la salida fácil pero insegura); en su lugar arma un bundle combinando el certificado raíz de `certifi` con el intermedio correcto, guardado en `certs/sectigo_rsa_ov_intermediate.pem`.

## Estructura

```
src/            scraper y parser
data/raw/       HTML crudo descargado (con hash para reproducibilidad)
data/processed/ artículos parseados en JSON
docs/experiments/  bitácora de experimentos
tests/          tests del parser
```

## Roadmap

- [x] Scraper + parser del piloto (Cap. III) a JSON por artículo
- [ ] Extender parser al CST completo (~500 artículos)
- [ ] Dataset de evaluación (factual directa, aplicación, vigencia, fuera de alcance)
- [ ] Baseline de recuperación (BM25 → embeddings → híbrido + reranking)
- [ ] Guardrails (filtros de entrada/salida, detección de fuera de alcance)
- [ ] Router por costo/dificultad y caché
