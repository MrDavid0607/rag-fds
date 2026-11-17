# Errores y limitaciones de la extracción (borrador de Fase 2)

Estado: **hallazgos automáticos y de muestreo del asistente**. La verificación contra los PDF la hace el autor
(columna `verificado_por_autor` de `verificacion_extraccion.csv`, Fase 3). Este archivo se completa en la Fase 3.

Extracción: Docling 2.150.1 + RapidOCR 3.10.0, 101 PDF, 1 134 páginas, 0 fallos de conversión.

## Hallazgos

| # | Hallazgo | Efecto | Mitigación / estado |
|---|---|---|---|
| 1 | Docling descarta encabezados y pies de página del Markdown. En muchas FDS la **versión y la fecha viven ahí** ("Versión: 1  Página 1/8"). | La versión/fecha no aparecen en `documento.md`. | `metadatos.py` las busca en el texto crudo del PDF (pypdfium2) y guarda la evidencia. Aun así 17 fichas no muestran versión y 67 no muestran fecha de revisión en el texto: quedan vacías, **no se infieren**. |
| 2 | En formularios con etiquetas y valores en columnas (p. ej. FDS 23-25), Docling **separa las etiquetas de sus valores** y los reordena ("Nombre del producto :" … "983" … "Tufcote 3.5 HH - Aluminum"). | El valor no queda pegado a su etiqueta; riesgo de leer un dato como si fuera otro. | `metadatos.py` rechaza valores numéricos como nombre de producto y usa el título de la página; revisar a mano estas fichas. |
| 3 | El encabezado repetido de cada página (nombre del producto) se emite como título `##` en cada página. | Ruido en la detección de secciones y en el chunking. | Se tratará en `secciones.py`/`chunking.py` (ignorar títulos repetidos idénticos). |
| 4 | Logos repetidos en el encabezado (hasta 8 copias idénticas por ficha). | Imágenes duplicadas sin valor técnico. | Se guarda una sola copia por huella SHA-1 y las repetidas se registran en `imagenes.json` (`duplicadas_no_guardadas`). |
| 5 | El conteo de tablas puede variar entre CPU y GPU para la misma ficha (FDS 71: 7 vs 6; FDS 80: 19 vs 18). | Pequeñas diferencias de estructura entre ejecuciones. | Las 101 fichas se procesaron con una sola configuración (PC, GPU). La verificación de tablas contra el PDF es obligatoria. |
| 6 | Docling escapa HTML y guiones bajos en el Markdown (`&amp;`, `\_`). | El texto crudo del Markdown no es idéntico al del PDF. | Se decodifica al construir chunks y metadatos (`html.unescape`, `\_` → `_`). |
| 7 | Los **pictogramas GHS** se guardan como imagen, pero el OCR **lee texto, no interpreta** su significado (una llama o un signo de exclamación no se convierten en "inflamable"/"irritante"). | El sistema RAG no puede responder qué pictograma tiene un producto a partir de la imagen. | Se conservan como imagen enlazada con página y sección aproximada; el significado solo se usa si el texto de la ficha lo dice (frase de peligro H…, palabra de advertencia). No se infiere. |
| 8 | Muchas FDS no nombran al fabricante en el contenido (15 de 101: FDS 1-4, 9, 11, 13-17, 23-25, 101). | `fabricante` vacío para esas fichas. | Se deja vacío con nota. El nombre de archivo a veces lo trae (p. ej. "PINTURAS BLER"), pero es procedencia, no contenido: **el autor decide** si lo completa. |
| 9 | RapidOCR emite el aviso "text detection result is empty" en imágenes sin texto (pictogramas, logos). | Ninguno: es el comportamiento esperado. | Sin acción. |

## Pendiente (Fase 3)

- Estado por sección (presente / fallo de extracción / ausente en el original) para las 101 fichas.
- Una tabla verificada por ficha, con pre-chequeo automático de números y unidades contra el texto crudo.
- `revision.html` y `verificacion_extraccion.csv` para la revisión manual del autor.
