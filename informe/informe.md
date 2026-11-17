# RAG sobre Fichas de Datos de Seguridad: comparación top-k 3 vs top-k 6

**Daniel Reyes, Sebastián Urrego y David Martínez** · Procesamiento de Lenguaje Natural, Universidad Sergio Arboleda, 2026 S02

## 1. Sistema y método

Se procesaron las **101 FDS** (1 134 páginas, 8 fabricantes) a Markdown con Docling, conservando tablas, página e imágenes; se dividieron en **6 483 fragmentos** (por sección, ~800 caracteres, solape 150, tablas enteras) y se indexaron con `bge-m3` en Chroma.
Las preguntas filtran por fabricante, año y producto antes de buscar. `qwen2.5:7b-instruct` responde solo con los fragmentos y cita `[n]`; el código construye la lista de fuentes (fabricante · producto · versión · documento · página · sección).
Todo corre con modelos locales de Ollama, sin APIs de pago (RTX 3050 de 4 GB). Se evaluaron **12 preguntas** (6 directas, 4 integradoras o comparativas, 2 sin respuesta; 9 secciones; una compara dos versiones del mismo producto) cuyas referencias (redactadas con asistencia de IA) tienen su evidencia comprobada automáticamente contra el texto del PDF; **su verificación humana está pendiente**, por lo que los resultados son provisionales.
Las dos configuraciones **solo difieren en top-k** (3 y 6); corpus, chunking, embeddings, generador, prompt y evaluador (`llama3.1:8b`, RAGAS 0.4.4, temperatura 0) son idénticos.

## 2. Comparación (10 preguntas respondibles)

| Configuración | Faithfulness | Context Precision | Context Recall | Casos válidos F/CP/CR | Respuestas «no hay evidencia» | Generación media |
|---|---|---|---|---|---|---|
| top-k 3 | 0.892 | 1.000 | 0.910 | 10/10/10 | 2 (e09, e10) | 20.6 s |
| top-k 6 | 0.867 | 1.000 | 1.000 | 10/10/**9** | 0 | 24.3 s |

Un cálculo falló (Context Recall de e09 con top-k 6: salida no interpretable del evaluador, dos intentos) y se registró como `NaN`, no como 0. La evaluación se corrió dos veces (v1 y v2, esta tras corregir un defecto de metadatos, ver §4): las 30 puntuaciones salieron idénticas. Context Precision vale 1.00 en los 20 casos: no discrimina. Top-k 6 recupera la evidencia de **ambas secciones o ambos documentos** en e07, e08 y e10, donde top-k 3 se queda corto;
su Faithfulness es algo menor, pero la causa está en el evaluador y en las citas (§3), no en datos inventados. Con 10 preguntas, una corrida y un evaluador de 8 B, esto es una **comparación didáctica**: no demuestra que una configuración sea mejor en general. Se elige **top-k 6** (+18 % de tiempo de generación).

## 3. Tres casos analizados

**e07 (comparación de versiones, Pintura Primera Mano & Acabado, Corona 2019 vs 2021).** Con top-k 3 falta el fragmento de la densidad de 2019 y la respuesta afirma que «no se menciona» (la ficha de 2019 sí la trae: 1371,4 kg/m³). Con top-k 6 la respuesta es correcta (36 → 12 meses de almacenamiento; 1371,4 → 1377,5 kg/m³).
Aun así RAGAS puntúa Faithfulness 0.50: declara no respaldada la afirmación 36 → 12 meses, aunque los contextos [1] y [2] contienen «12 meses» y «36 meses» (falso negativo del evaluador). *Revisión asistida por IA contra el PDF: con top-k 6 los cuatro datos y las cuatro citas son correctos; con top-k 3 la afirmación sobre 2019 es falsa. Confirmación del autor pendiente.*

**e04 (Sigmadur One Buff 3142, PPG: % y CAS del dióxido de titanio).** Respuesta con el dato correcto (7 - <10 %, CAS 13463-67-7) en ambas configuraciones, pero Faithfulness 0.50: el evaluador considera no respaldado que «su número CAS» sea 13463-67-7, porque el contexto lo asigna al dióxido de titanio y no al producto.
Es literalidad del evaluador ante una redacción ambigua. *Revisión asistida por IA: datos y citas (FDS 65, pág. 3, sección 3) correctos en ambas configuraciones. Confirmación del autor pendiente.*

**e09 (comparación de dos productos de Pintuco por toxicidad para la reproducción y categoría de inflamabilidad).** Es el caso más débil. El filtro devuelve 6 productos (en comparaciones se desactiva el estrechamiento por código numérico) y recupera la sección 11 en lugar de la 2, donde están H360 y H225/H226.
Con top-k 3 el sistema dice «no hay evidencia» y a la vez afirma que ambos no cumplen criterios; con top-k 6 acierta la toxicidad del Pintulaca Rojo Claro pero **omite la categoría de inflamabilidad** y cita fichas de otros esmaltes para el 1772. Context Recall con top-k 6 falló (`NaN`) en ambas corridas, y un diagnóstico paso a paso dio Faithfulness 1.00 frente a 0.67 de la corrida oficial (el valor depende del procedimiento de llamada). *Revisión asistida por IA contra el PDF: con top-k 6 lo que dice es correcto pero incompleto y 4 de las 5 citas de la segunda afirmación son de otras fichas; con top-k 3 atribuye al Pintulaca Rojo Claro (que sí tiene H360) lo que dice otra ficha, es incorrecta. Confirmación del autor pendiente.*

## 4. Preguntas sin respuesta y limitaciones

- **e11** (rendimiento del Acrolatex, que la FDS no trae): reconoce la falta de evidencia con ambas configuraciones. **e12** (Intergard 475HS, producto inexistente): en v1 **inventó** con ambas, atribuyéndole primeros auxilios de otras fichas de International; en v2, con los nombres de producto corregidos, **reconoce** la falta de evidencia con ambas. Es un resultado frágil: el filtro por producto y el aviso de «producto sin ficha» siguen sin activarse en ese caso.
- Extracción: Docling descarta encabezados y pies (versión y fecha); en formularios separa etiquetas y valores; el OCR no interpreta pictogramas (8 tablas con íconos leídos como ideogramas); 15 fichas no nombran al fabricante y 17 no traen versión (no se infieren). Una comprobación asistida por IA de las 1 248 tablas halló 20 problemas reales (14 fichas); el más grave: en la FDS 31, parcialmente rasterizada, una fila de la tabla de composición perdió sus códigos de peligro (H350, H340…). La verificación humana de la extracción está pendiente.
- 8 fichas de AkzoNobel tenían el nombre de producto mal extraído («X International.»); se corrigió, se reconstruyó el índice y se repitió la evaluación completa (v2): solo cambió e12; los datos de v1 se conservan.
- El evaluador local es ruidoso: no determinista, una salida inválida y Context Precision siempre en 1.00. Faithfulness no mide completitud.
- Arquitectura: el Learner Lab niega instancias mayores a *large*; en la EC2 `r5.large` la generación daba 1.7 tokens/s y la extracción 17 s/página, por lo que se trabajó en el PC con GPU (8.3 tokens/s; 2.4 s/página). El costo AWS fue menor a US$ 1.

## 5. Conclusión

El sistema responde con citas trazables y reconoce la falta de evidencia en la mayoría de los casos, pero un generador de 7 B puede omitir datos, citar fichas ajenas o, ante un producto inexistente, inventar (como en v1) o acertar por motivos frágiles (v2). En este conjunto top-k 6 resultó más completo que top-k 3 en preguntas que integran secciones o documentos,
a un costo moderado, y es la configuración elegida. Las puntuaciones de RAGAS orientan, pero requieren revisión manual; las demás mejoras identificadas (estrechar por código en comparaciones, priorizar la sección 2 para clasificaciones, avisar ante productos no encontrados)
no se aplicaron para no ajustar el sistema a las preguntas de evaluación.
