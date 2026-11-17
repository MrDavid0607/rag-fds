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

## Hallazgos de la Fase 3 (secciones y tablas)

| # | Hallazgo | Fichas | Tratamiento |
|---|---|---|---|
| 10 | **Encabezado de sección dentro de un párrafo.** Una marca de agua ("COPIA CONTROLADA") hace que Docling funda el encabezado con el texto vecino. El texto está en el Markdown pero ya no como título. | FDS 100 (secc. 5 y 7), FDS 101 (secc. 5 y 15) | `secciones.csv` las marca `fallo_extraccion` (el encabezado sí está en el PDF). El chunking debe detectar el encabezado también dentro de un párrafo. |
| 11 | **Numeración antigua (norma NTC):** 2 = composición, 3 = identificación de riesgos. | FDS 1-4, 9, 13-17 | La sección se identifica por su **título**, no por el número; `numero_en_documento` guarda el número real. |
| 12 | Una ficha tiene "Primeros auxilios:" como título **sin número**. | FDS 2 | Se acepta como presente con la nota "(sin número)". |
| 13 | **El OCR leyó íconos pequeños como ideogramas** (日, 回, 新) dentro de celdas de tablas de composición (columna junto a "<5 %", nombres de sustancias). | FDS 60, 68, 76, 89, 91, 94 | Detectado por el pre-chequeo. Es el mismo problema de pictogramas (limitación 7): la imagen no es texto. Se corrige a mano o se ignora ese carácter al construir chunks. |
| 14 | 4 fichas no tienen ninguna tabla en el Markdown. | FDS 2, 15, 16, 17 | El autor revisa un bloque con datos (sección 3 o 9) en lugar de una tabla. |
| 15 | Valores sueltos que el Markdown no reproduce o reproduce distinto. | FDS 11, 14, 31, 98 | Marcadas `REVISAR`. |
| 16 | **Nombre de producto mal extraído en 8 fichas de AkzoNobel/International** (FDS 82, 83, 84, 85, 95, 96, 98, 99): `producto` quedó como «X International.» o «International. X» (el logo del encabezado leído por el OCR). Se detectó en la Fase 7, al ver la lista de fuentes de la pregunta e12. | FDS 82, 83, 84, 85, 95, 96, 98, 99 (efecto: no se podían filtrar por producto y el encabezado de sus fragmentos llevaba el nombre equivocado) | **Corregido** el 2026-11-17: `metadatos.py` ahora descarta líneas formadas solo por «X» e «International»; los 8 productos pasaron a su nombre real (p. ej. «ZINC PRIMER 10844 GRIS PARTE A») sin cambiar ningún otro metadato. Se reconstruyeron los fragmentos y el índice y se **repitió la evaluación completa**; los resultados anteriores se conservan en `eval/v1_antes_correccion_metadatos/`. |
| 17 | **FDS 31 está parcialmente rasterizada** (tablas como imagen leídas por OCR). En la tabla de composición de la pág. 2, la fila de «Nafta (petróleo), fracción pesada tratada con hidrógeno» **perdió sus códigos de peligro** (PDF: «Carc. 1B: H350; Muta. 1B: H340; Tox. Agud. 5: H313; Tox. Asp. 1: H304»; Markdown: «Car. - H : M. : : Mgro»). Hallado en la revisión asistida por IA (comprobación de las 1 248 tablas + inspección visual). | FDS 31 (pág. 2; págs. 4 y 5 sin capa de texto pero con OCR correcto en la pág. 5) | **Sin corregir**; limitación documentada. El autor debe mirar esta ficha. Detalle en `verificacion/revision_asistida_ia.md`. |
| 18 | Texto basura de OCR dentro de tablas (p. ej. «6RTo», «6Bto», «ORTO», «Alln», «00») y 8 tablas con íconos leídos como ideogramas (ver 13). | FDS 10, 21, 27, 34, 42, 75 (basura); 60, 68, 70, 75, 76, 89, 91, 94 (ideogramas) | Baja gravedad; los ideogramas se eliminan al construir los fragmentos. |

### Resultado de la detección de secciones (101 fichas × 16 = 1 616)
`presente` 1 612 · `fallo_extraccion` 4 · `ausente_en_original` 0. Todas las secciones se encontraron en el PDF en las 101 fichas;
no hay ninguna marcada como ausente. Hay que dar fe de eso mirando al menos las fichas 100 y 101, y la FDS 2.

### Resultado del pre-chequeo de tablas (1 tabla por ficha)
`OK` 87 · `REVISAR` 10 · `SIN_TABLA` 4. Se verifican tres cosas: que cada número y unidad de la tabla exista en el texto crudo del PDF de esa
página, que cada palabra de las celdas exista allí, y que no falten números de las mismas líneas del PDF. Se probó con mutaciones
(cambiar un número, una unidad o borrar una fila): detecta las tres.
**Límite:** `OK` no significa "verificado". El pre-chequeo no ve valores presentes pero en la celda equivocada, columnas intercambiadas
ni filas mezcladas; eso solo lo detecta la revisión humana. La columna `verificado_por_autor` está **vacía** y la llena el autor.

## Verificación humana de la extracción (muestra de 24 fichas, 2026-11-17)

**Método mixto, declarado como tal.** (1) El 100 % de las tablas de las 101 fichas (1 248) se comprobó automáticamente contra el texto del PDF y se revisó con asistencia de IA (`revision_asistida_ia.md`).
(2) El **autor verificó visualmente 24 fichas** con `verificacion/revision_muestra/index.html`: las 14 con hallazgos reales de la IA y 10 al azar (semilla 7). Registro exportado: `verificacion/verificacion_extraccion_muestra_autor.json`;
volcado en `verificacion_extraccion.csv` (columnas `verificado_por_autor`, `errores_encontrados`, `observaciones`). Las otras 77 fichas **no** tienen verificación humana.

| Resultado del autor | Fichas |
|---|---|
| **Coincide** (13) | FDS 7, 21, 23, 27, 34, 42, 49, 54, 58, 60, 70, 75, 99 |
| **Tiene errores** (11) | FDS 10 («falta protección del cuerpo y pies y ducha de emergencia»), 31 («faltan códigos y número en nafta»), 68, 76, 91 («símbolo raro en vez de %»), 89 («símbolos raros adicionales»), 94 («confunde íconos con símbolos raros»), 11, 81 y 87 (sin descripción), 15 («no hay markdown») |

Lectura (con las salvedades del caso):
- **Coinciden con la revisión asistida por IA** 6 de las 14 fichas con hallazgos (FDS 10, 68, 76, 89, 91 y 94) más la FDS 31 (el autor marcó «ok» pero su nota describe el error; se registró `con_errores` por coherencia y queda por confirmar).
- **Discrepancias:** en 7 fichas con hallazgo menor de la IA (FDS 21, 27, 34, 42, 60, 70, 75) el autor marcó «coincide» (texto basura de OCR o un ideograma que la IA sí vio). Son defectos de baja gravedad que el autor no consideró errores.
- **FDS 10:** la IA ve el contenido de protección corporal y de pies y la ducha de emergencia, pero con los rótulos de los pictogramas mezclados en la misma fila; no ve filas ausentes.
- **FDS 81 y 87:** el autor marcó errores sin describirlos; la IA comparó las tablas de composición de la pág. 3 con el PDF y coinciden fila a fila. El error visto no se pudo identificar. Lo mismo para la **FDS 11** (la IA solo ve celdas combinadas duplicadas).
- **De las 10 fichas al azar, 4 quedaron con errores** (11, 15, 81, 87) y la revisión automática solo había señalado dos de ellas. Es una advertencia: **la revisión automática no sustituye la visual**, y la tasa de fichas con errores en la extracción podría ser mayor a la que sugiere el 3 % de tablas con hallazgos.
- Pendiente (opcional): que el autor precise qué vio en las FDS 11, 81 y 87.

## Pendiente

- Revisión manual del autor (6 tandas de 20 en `verificacion/revision/`).
- Resumen final de errores al cerrar la revisión humana.
