# 003 — Separar "parsear todo" de "filtrar por rango"

**Qué cambió:** `parse_chapter(html_path, chapter, article_range)` era una sola función que mezclaba dos responsabilidades: recorrer el HTML construyendo un `Article` por cada encabezado, y decidir cuáles de esos artículos quedaban dentro del rango pedido. El corte de rango dependía de una bandera (`past_end`) que solo se activaba al procesar un párrafo de **cuerpo** del último artículo del rango.

**El bug que esto escondía:** si el último artículo de un rango no tenía ningún párrafo de cuerpo separado (título y todo en el mismo `<p>` que el encabezado, sin nada después antes del siguiente `ARTICULO`), `past_end` nunca se activaba y el parseo seguía de largo hasta el final del documento, colando artículos fuera del rango pedido sin ningún aviso.

**El cambio:** se partió en dos funciones puras:
- `parse_all_articles(html_path, chapter)` recorre **todo** el documento y devuelve la lista completa de artículos, sin ninguna noción de rango.
- `filter_range(articles, start_id, end_id)` recibe esa lista ya armada y la recorta por índice, buscando `start_id` y `end_id` explícitamente. Si alguno de los dos no aparece, lanza `ValueError` en vez de devolver silenciosamente una lista vacía o a medias.

`parse_chapter` ahora es un wrapper de una línea sobre las dos anteriores, para no romper las llamadas existentes.

**Por qué importa más allá de arreglar el bug:** tener `parse_all_articles` como función independiente es exactamente lo que hace falta para el resto del roadmap — extender al CST completo (~500 artículos) ya no requiere tocar la lógica de parseo, solo dejar de filtrar, o filtrar por capítulo/rango distinto cada vez.

**Verificación:** se agregó un test que reproduce el escenario exacto del bug (artículo final del rango sin párrafos de cuerpo) y confirma que ya no se cuela el artículo siguiente. Se regeneró el JSON procesado del piloto y se comparó byte a byte contra el anterior: sin cambios, como se esperaba de un refactor que no debía alterar el resultado.
