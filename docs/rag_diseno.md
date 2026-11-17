# Diseño del sistema RAG (Fase 4)

Todo se ejecuta con modelos locales de Ollama en el PC del autor (GPU RTX 3050 de 4 GB). No se usa ninguna API de pago.

## Parámetros documentados

| Elemento | Valor | Dónde se fija |
|---|---|---|
| Corpus | 101 FDS (1 134 páginas) en Markdown (`data/processed/`) | — |
| Fragmentos | **6 483** (5 140 de texto + 1 343 tablas); largo mediano 713 caracteres, p95 920, máx 2 548 | `indice/manifiesto.json` |
| Estrategia de chunking | Por **sección de la FDS** y luego por tamaño; las tablas no se parten | `src/rag_fds/chunking.py` |
| Tamaño / solape | **~800 caracteres / 150 de solapamiento** (en límites de frase); tabla ≤ 1 500 caracteres, si no, se divide por filas repitiendo el encabezado | `config/base.yaml` |
| Encabezado de cada fragmento | `[fabricante · producto · versión · FDS año · Sección N: nombre]` dentro del texto y en los metadatos | `chunking.py` |
| Metadatos por fragmento | doc_id, fabricante, producto, versión, fecha de revisión, año de la carpeta, archivo, páginas, sección (número y nombre), tipo (texto/tabla), imágenes de las mismas páginas | índice Chroma |
| Embeddings | `bge-m3` (Ollama, 1024 dim, digest `790764642607…`) | `config/base.yaml` |
| Índice | Chroma persistente, métrica coseno, colección `fds` (indexado en 272 s, 23.8 fragmentos/s) | `indice/chroma/` |
| top-k | **3** (`config/topk3.yaml`) y **6** (`config/topk6.yaml`); lo único que difiere | `config/` |
| Generador | `qwen2.5:7b-instruct` (Q4_K_M), temperatura 0, semilla 42, `num_ctx` 8 192, `num_predict` 700 | `config/base.yaml` |
| Prompt | Fijo en `config/base.yaml` (usar solo los fragmentos, citar `[n]`, decir cuando no hay evidencia) | `config/base.yaml` |

`config/topk3.yaml` y `config/topk6.yaml` heredan `base.yaml` y solo cambian `top_k`. `rag_fds.config.verificar_solo_topk` lo comprueba por código.

## Cómo responde

1. **Filtros por metadatos antes de buscar** (`rag.py`): se detectan en la pregunta el fabricante (con alias, p. ej. International → AkzoNobel), el año
   (2018-2025) y el producto (por las palabras raras de su nombre). Si hay producto, solo se busca en sus fichas.
2. **Comparaciones**: si la pregunta compara productos o versiones, se recupera **por documento/producto** y los `k` lugares se reparten entre ellos
   (así ninguno queda sin contexto, y el total sigue siendo `k`).
3. **Sección probable**: si el tema sugiere una sección (p. ej. "extinción" → 5), los fragmentos de esa sección reciben una pequeña ventaja
   (`bonus_seccion`, 0.06 de distancia); no se excluye nada.
4. **Generación con citas**: el modelo cita `[n]`; la lista de **fuentes la construye el código** con los metadatos de los fragmentos citados
   (fabricante · producto · versión · documento · página · sección) y marca las citas a fragmentos inexistentes.
5. **Evidencia insuficiente**: el prompt exige responder "No hay evidencia suficiente en las FDS disponibles para…" cuando falta el dato; la
   interfaz lo señala. Si la pregunta nombra una variante sin ficha (p. ej. "Viniltex Advanced" cuando solo existe "Viniltex Pro 650"), el sistema
   añade un aviso determinista al prompt.

Uso: `python -m rag_fds.rag "pregunta" --config config/topk6.yaml` y `streamlit run app/demo.py --server.address 127.0.0.1` (solo escucha en local).

## Prueba con preguntas de desarrollo (eval/preguntas_desarrollo.json)

Seis preguntas distintas a las de evaluación; resultados completos en `eval/desarrollo_topk6.json` y `eval/desarrollo_topk3.json`. Lo que se observó:

| Pregunta | top-k 6 | top-k 3 |
|---|---|---|
| dev01 cinc en polvo, Dimetcote 302H | Correcta ("30 - <60 %"), cita la tabla de la sección 3 | Correcta pero omite el "<" ("30% y 60%") |
| dev02 primeros auxilios ojos, Koraza | Correcta | Correcta |
| dev03 teléfono de emergencia, Sikafloor-2430 A | Da solo "01 8000 916012" (el número CISPROQUIM de Bogotá no aparece) y cita además un fragmento irrelevante [4] | Igual, cita [1][3] |
| dev04 medios de extinción, Topcoat 400 1793 | Correcta | Correcta (omite "no usar chorro de agua") |
| dev05 comparar Pintura Total 2021 vs 2023 | Correcta: 6 vs 12 meses de almacenamiento y la frase de manipulación manual de cargas, citadas [3][5]; los datos coinciden con el Markdown | **Incorrecta**: habla de "versión 2021 vs 2019" (no existe esa comparación) |
| dev06 sin respuesta ("Viniltex Advanced") | Reconoce que solo hay datos de Viniltex Pro 650 | Igual |

Conclusiones provisionales (**falta la verificación del autor contra los PDF**): con top-k 3 la comparación entre dos documentos recibe solo 1-2 fragmentos por
documento y el generador mezcla datos; con top-k 6 respondió bien esa pregunta. Es una observación de 6 preguntas, no una prueba.

## Problemas encontrados y cómo se trataron

- **El generador de 7B rechaza con demasiada facilidad** cuando el prompt es largo y estricto: con un prompt de 9 reglas respondió "No hay evidencia" a preguntas cuyo dato estaba
  en el contexto (dev02, dev03). Se simplificó el prompt y desaparecieron esos rechazos. El prompt final queda fijo antes de la evaluación.
- **Solo con prompt, una pregunta sin respuesta se contestó con datos de otro producto** (dev06). Se añadió la detección determinista de variantes sin ficha.
- **Etiquetas y valores separados** en algunas FDS (formularios): el dato está en el fragmento pero desordenado; el prompt lo advierte. dev03 muestra que el modelo aún lo resuelve a medias.
- **Tablas con celdas repetidas y separadores de cientos de guiones** inflaban los fragmentos hasta 5 000 caracteres; se colapsan (máximo actual 2 548).
- **Latencia de recuperación**: 0.05-0.3 s con `bge-m3` ya cargado, pero ~7 s cuando Ollama debe volver a cargarlo después del generador (VRAM de 4 GB).

## Limitaciones conocidas

- Los 15 documentos sin fabricante en el contenido no aparecen al filtrar por fabricante (no se infiere desde el nombre de archivo).
- La detección de producto usa el nombre extraído por `metadatos.py`; un nombre mal extraído impide el filtro (la búsqueda sigue funcionando sin filtro).
- Las imágenes que se muestran son las de las mismas páginas del fragmento citado; no se afirma que ilustren ese texto ni se relacionan con tablas sin evidencia.
- Con 7B y cuantización Q4 el generador puede omitir datos o mezclar versiones; por eso la revisión manual de las citas es obligatoria (Fase 7).

## Validación humana de citas de la demo (2026-11-17)

El autor comprobó contra los PDF las citas de dos consultas hechas en la app (top-k 6) y **coincidieron**:

| Consulta | Qué se comprobó |
|---|---|
| Medios de extinción del Topcoat 400 1793 Blanco | FDS 80, pág. 4, sección 5: polvos químicos secos, CO₂, agua pulverizada o espuma; no usar chorro de agua |
| Comparación de la Pintura Primera Mano & Acabado (Corona) 2019 vs 2021 | FDS 29 pág. 3 «36 meses» y pág. 5 «1371,4 kg/m³»; FDS 43 pág. 3 «12 meses» y pág. 5 «1377,5 kg/m³»; cada cita apunta a su ficha y página |

Es una muestra de dos consultas; la revisión de citas de los 5 casos de la evaluación está en eval/revision_manual_resultados_autor.md.

