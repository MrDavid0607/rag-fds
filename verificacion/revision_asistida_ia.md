# Revisión asistida por IA de la extracción (Fase 3)

**Qué es y qué no es.** Claude comprobó automáticamente **todas** las tablas de las 101 fichas (1 248 tablas, no solo una por ficha) contra el texto crudo del PDF de su página y miró a ojo algunas páginas.
**No es la verificación del autor**: `verificado_por_autor` en `verificacion/verificacion_extraccion.csv` sigue vacía. Ese CSV ahora tiene dos columnas más (`revision_asistida_ia`, `notas_revision_asistida`).

Método (`python -m rag_fds.revision_asistida_extraccion`): por tabla, (a) cada número del Markdown debe existir en el texto del PDF de esa página, (b) cada palabra de las celdas debe existir allí, (c) no debe haber caracteres que no sean del alfabeto latino/griego/unidades (íconos leídos como ideogramas).
Detalle por tabla: `verificacion/revision_asistida_tablas.csv`.

## Resultado
- **1 248 tablas revisadas; 37 con algún hallazgo (3.0 %) en 29 fichas; 72 fichas sin ningún hallazgo.**
- De los 37: **17 son falsos positivos** (enlaces a imágenes dentro de celdas, subíndice de CO₂, símbolo ˚, nombre del fabricante en un logo leído por el OCR, «FLAMMABLE LIQUID» en una etiqueta de transporte) y **20 son hallazgos reales**, agrupados en 14 fichas:

| Tipo | Tablas | Fichas | Gravedad |
|---|---|---|---|
| Íconos leídos como ideogramas (日 回 风 十 新) | 8 | FDS 60, 68, 70, 75, 76, 89, 91, 94 | Baja: el carácter se elimina al construir los fragmentos |
| Texto basura de OCR en tablas de EPP o similares («6RTo», «6Bto», «ORTO», «Alln», «00») | 6 | FDS 10, 21, 27, 34, 42, 75 | Baja |
| **FDS 31 (PDF parcialmente rasterizado)**: tablas como imagen leídas por OCR | 6 | FDS 31 | **Alta en la pág. 2** (ver abajo) |

### El hallazgo importante: FDS 31, página 2 (verificado con la imagen de la página)
La tabla de composición del *Recubrimiento antigraffiti* (Corona) es una **imagen** en el PDF. En el Markdown, la fila de «Nafta (petróleo), fracción pesada tratada con hidrógeno»
perdió sus códigos de peligro: el PDF dice «Carc. 1B: H350; Muta. 1B: H340; Tox. Agud. 5: H313; Tox. Asp. 1: H304 - Peligro» y el Markdown dice «Car. - H : M. : : Mgro». Es una **pérdida de información de seguridad** (la clasificación carcinogénica).
Las filas de los otros dos ingredientes (CAS 64742-47-8 y 1760-24-3) y las concentraciones sí coinciden. La tabla de EPP de la pág. 5 se comparó con la imagen y coincide. **Sin corregir** (no se edita a mano el Markdown extraído; queda como limitación documentada); el autor debe mirar esta ficha.

### Falsos positivos descartados tras revisar el PDF
- FDS 11: el «9» que faltaba era el pie de página «Página 1 de 9».
- FDS 14: «1 9.60» aparece así en el propio PDF (error tipográfico de la ficha), el Markdown es fiel.
- FDS 98: «4.4» pertenece al nombre químico «fenol,4,4´-…».

## Qué debe hacer el autor
Abrir `verificacion/revision/` y comprobar, como mínimo, **la ficha 31** (págs. 2, 4 y 5), una ficha con ideogramas (p. ej. la 94, pág. 2) y 3-4 fichas al azar, y llenar `verificado_por_autor`.
Para la guía basta con haber verificado al menos una tabla o bloque por ficha: esa verificación humana sigue **pendiente**.
