# Guion de la demostración

## 0. Antes de empezar (5 minutos)

1. Cierra programas que usen la GPU (juegos, Parsec): la RTX 3050 tiene solo 4 GB y se reparte entre `bge-m3` y el generador.
2. Comprueba que Ollama responde y tiene los modelos:
   ```bash
   ollama list        # debe mostrar bge-m3, qwen2.5:7b-instruct y llama3.1:8b
   ```
3. Desde la raíz del repo, con el entorno activo, arranca la demo (solo escucha en local):
   ```bash
   set PYTHONPATH=src
   streamlit run app/demo.py --server.address 127.0.0.1 --server.port 8501
   ```
   Abre <http://127.0.0.1:8501>. **Haz una consulta de calentamiento** antes de la presentación: la primera carga los modelos (~15-30 s extra).
4. En la barra lateral deja **top-k = 6** (configuración elegida) y ten a mano la de top-k 3 para comparar.
5. Ten abiertos los PDF de las fichas que vas a mostrar (carpeta `data/raw/FDS EVALUADAS/`) para enseñar que cada cita apunta a la página correcta.
6. La EC2 **no hace falta** para la demo; está detenida. Si el docente pregunta: `infra/estado.sh` (necesita credenciales vigentes del Learner Lab).

## 1. Recorrido sugerido (≈ 8 minutos)

| # | Pregunta (botón de ejemplo o escribirla) | Qué mostrar |
|---|---|---|
| 1 | *¿Qué medios de extinción son adecuados para el Topcoat 400 1793 Blanco de International?* | Respuesta corta con `[2][3]`; la lista de **fuentes** (fabricante · producto · versión · documento · página · sección); los fragmentos recuperados en orden y el filtro aplicado (producto 1793, no el 1772). Abre el PDF en la página 4 y confirma la frase. |
| 2 | *¿Cuál es el teléfono de emergencia del proveedor del Sikafloor-2430 Part A?* | Caso de **formulario** (etiqueta y valor separados en el Markdown): el sistema da un número y omite el de Bogotá. Es un buen momento para explicar la limitación de la extracción. |
| 3 | *Compara la Pintura Primera Mano & Acabado de Corona entre la ficha de 2019 y la de 2021: tiempo máximo de almacenamiento y densidad a 20 ºC.* | **Comparación de versiones**: la app recupera por documento (un fragmento de cada ficha); respuesta 36 → 12 meses y 1371,4 → 1377,5 kg/m³ con citas distintas. Cambia a top-k 3 y muestra que puede perder el dato de 2019. |
| 4 | *¿Cuál es el rendimiento teórico en m² por galón del Acrolatex 50 3508 de Pintuco?* | **Sin evidencia**: «No hay evidencia suficiente en las FDS disponibles para…», sin fuentes. Explica que las FDS no traen rendimiento (eso va en fichas técnicas). |
| 5 | *¿Cuál es el punto de inflamación del producto Viniltex Advanced de Pintuco?* | **Producto parecido que no existe**: el aviso de «variante sin ficha» y la respuesta que reconoce que solo hay Viniltex Pro 650. |

**Honestidad con el límite conocido:** si te piden un producto que no existe y no se parece a ninguno (p. ej. *Intergard 475HS de International*), en la primera evaluación (v1) el sistema **inventó** con primeros auxilios de otra ficha; tras corregir los nombres de producto de 8 fichas (v2) reconoce la falta de evidencia, pero es un resultado frágil (el filtro y el aviso no se activan). Dilo tú antes de que te lo encuentren: está en `eval/analisis_resultados.md` y en el informe.

## 2. Preguntas probables del docente (respuesta corta)

- **¿Por qué no usaron la EC2 para todo?** El Learner Lab deniega instancias mayores a *large*; en la `r5.large` el generador daba 1.7 tokens/s y la extracción 17 s/página. En el PC con GPU: 8.3 tokens/s y 2.4 s/página. Se dejó la EC2 para la infraestructura reproducible por CLI y se mantiene detenida; costo AWS < US$ 1.
- **¿Qué es un RAG y qué hace cada parte aquí?** Extrae y trocea las FDS (Docling + chunking), las indexa con embeddings (`bge-m3` + Chroma), recupera los fragmentos más cercanos a la pregunta y se los entrega a un LLM (`qwen2.5:7b`) que responde citándolos.
- **¿Cómo dividieron los documentos?** Por sección de la FDS y luego por tamaño: ~800 caracteres, solape 150, sin partir tablas. 6 483 fragmentos con fabricante · producto · versión · sección en el texto y en los metadatos.
- **¿Cómo garantizan las citas?** El modelo escribe `[n]`; el **código** arma la lista de fuentes con los metadatos del fragmento citado y marca citas inexistentes. La correspondencia con el PDF la verifica el autor a mano.
- **¿Cómo diferencian fabricantes, productos y versiones?** Filtros por metadatos antes de buscar (fabricante, año, producto) y recuperación por documento en las comparaciones.
- **¿Qué pasa si no hay evidencia?** El prompt exige decir «No hay evidencia suficiente…»; funciona en e11, en el caso Viniltex y (en v2) en e12; con productos inexistentes sin parecido es frágil (en v1, e12 inventaba).
- **¿Qué miden Faithfulness, Context Precision y Context Recall?** Faithfulness: qué parte de las afirmaciones de la respuesta está respaldada por los contextos. Context Precision: si los fragmentos pertinentes aparecen primero (con la respuesta de referencia). Context Recall: si los contextos cubren la información de la referencia.
- **¿Por qué el evaluador es otro modelo?** Para reducir el sesgo de autoevaluación: generador `qwen2.5:7b`, evaluador `llama3.1:8b`, ambos locales.
- **¿Qué configuración eligieron y por qué?** top-k 6: Context Recall 1.00 frente a 0.91 y recupera ambas secciones o documentos en las preguntas que integran dos; cuesta ~18 % más de tiempo de generación. Son 10 preguntas: comparación didáctica, no prueba general.
- **¿Qué falló en la evaluación?** Un cálculo de RAGAS (Context Recall de e09 con top-k 6, JSON inválido) se registró como `NaN`, no como 0; Context Precision es siempre 1.00 (no discrimina) y el evaluador tiene ruido (e07 y e09).
- **¿Qué no se infiere?** Fabricante, versión y fecha salen del texto del PDF con su evidencia; si no aparecen quedan vacíos (15 fichas sin fabricante, 17 sin versión). Las secciones ausentes se distinguen de los fallos de extracción (hubo 4 fallos y ninguna ausente).
- **¿Qué hacen con los pictogramas?** Se conservan como imagen con página y sección; el OCR lee texto, no interpreta el significado del pictograma, así que el sistema solo responde sobre ellos si el texto de la ficha lo dice.
- **¿Qué mejorarían?** Mantener el estrechamiento por código en comparaciones, priorizar la sección 2 para clasificaciones y avisar siempre que el producto nombrado no exista; después, repetir la evaluación completa (~65 min). (Los metadatos de 8 fichas de AkzoNobel ya se corrigieron y la evaluación se repitió: v1 vs v2 en `eval/analisis_resultados.md`.)
- **¿Por qué hay dos evaluaciones?** v1 reveló un defecto de datos (nombre de producto mal extraído en 8 fichas); se corrigió, se reconstruyó el índice y se repitió todo (v2). Las puntuaciones salieron idénticas y solo cambió e12; se conservan ambas versiones.
- **¿Qué parte la hizo Claude Code?** Código, scripts, documentación y análisis; las referencias de las 12 preguntas tienen su evidencia comprobada automáticamente contra el PDF y el autor las verificó contra los PDF; la extracción y los 5 casos analizados solo tienen revisión asistida por IA (falta la verificación humana); el autor debe poder explicar cada decisión (declarado en el README).
