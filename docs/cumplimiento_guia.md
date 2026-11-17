# Cumplimiento de la guía del parcial (RAG con FDS) — dónde está cada cosa

Estados: ✅ cumplido · ⚠️ cumplido con una limitación documentada · ⏳ pendiente de una verificación **humana** del autor (hay revisión automática o asistida por IA, pero no es la del autor).
Guía original: `docs/guia/RAG_FDS.pdf`. Resumen de arquitectura, decisiones y resultados: `README.md`.

## Corpus y extracción (30 %)

| Requisito de la guía | Dónde está la evidencia | Estado |
|---|---|---|
| Procesar e incorporar **las 101 FDS**, registrando procedencia y versión | `data/processed/<doc_id>/` (101 carpetas con `documento.md`, `imagenes/`, `imagenes.json`, `meta.json`). `meta.json`: archivo original, carpeta/año, sha256, fabricante, producto, versión, fecha, páginas, herramienta. Versión sin dato en 17 fichas y fabricante en 15: se dejan vacíos con nota (`verificacion/metadatos.csv`), nunca se infieren | ⚠️ |
| Pipeline PDF → Markdown | `src/rag_fds/extraccion.py` (Docling 2.150.1 + RapidOCR); métricas en `metricas/extraccion_resumen.md` (≈ 40 min, 0 fallos) | ✅ |
| Preservar títulos, tablas, listas, notas, unidades y referencias | Marcas `<!-- pagina: N -->` y tablas en Markdown; limitaciones en `verificacion/errores_extraccion.md` (18 hallazgos) | ⚠️ |
| Verificar contra cada PDF al menos una tabla o bloque y **registrar errores** | `verificacion/verificacion_extraccion.csv` (101 fichas: tabla elegida, resultado automático, diferencias); `verificacion/revision/` (PDF al lado del Markdown, 6 tandas de 20); `verificacion/revision_asistida_ia.md` (comprobación de las **1 248 tablas** + inspección visual); errores en `errores_extraccion.md` (p. ej. FDS 31 pág. 2). La columna `verificado_por_autor` está vacía | ⏳ |
| Identificar las secciones presentes entre las 16; distinguir ausentes de fallos de extracción; sin inferir | `verificacion/secciones.csv` (1 616 filas: 1 612 presentes, 4 fallos de extracción, 0 ausentes) y `src/rag_fds/secciones.py` | ✅ |

## Imágenes y trazabilidad

| Requisito | Evidencia | Estado |
|---|---|---|
| Conservar los elementos visuales con información técnica y enlazarlos por **rutas relativas** | `data/processed/<doc_id>/imagenes/` + enlaces `![…](imagenes/pXXX_imgYY.png)` en `documento.md` (0 rutas absolutas; los logos repetidos se guardan una sola vez) | ✅ |
| Registrar documento, página y sección de cada imagen | `imagenes.json` por ficha: archivo, **página**, **`seccion_num` y `seccion_nombre`**, tamaño (1 192 imágenes) | ✅ |
| Asociar una imagen con una tabla solo si hay evidencia | `relacion_con_tabla: null` en todas: no se afirma ninguna relación | ✅ |
| OCR donde haga falta y limitaciones con pictogramas | RapidOCR en imágenes; limitación 7 y 13 de `errores_extraccion.md` (el OCR lee texto, no interpreta pictogramas; íconos leídos como ideogramas en 8 tablas) | ⚠️ |

## RAG (25 %)

| Requisito | Evidencia | Estado |
|---|---|---|
| RAG funcional con modelos locales | `src/rag_fds/rag.py`, `app/demo.py`; Ollama local (`bge-m3`, `qwen2.5:7b-instruct`) | ✅ |
| Documentar chunking, tamaño, solapamiento, embeddings y top-k | `docs/rag_diseno.md` y `README.md` §4: ~800 caracteres, solape 150, tablas enteras, 6 483 fragmentos, `bge-m3`, top-k 3 y 6; `config/` | ✅ |
| Consultas sobre todas las FDS diferenciando fabricantes, productos y versiones | Filtros por metadatos y recuperación por producto/documento en comparaciones (`rag.py`); ejemplo: comparación 2019 vs 2021 en `informe/guion_demo.md` | ✅ |
| Cada afirmación vinculada a fabricante, producto, **documento, página y sección** | El modelo cita `[n]` y el **código** arma la lista de fuentes (`rag.fuentes`); visible en la demo y en `eval/respuestas_topk*.json` | ✅ |
| Indicar cuándo la evidencia es insuficiente; limitaciones y mitigaciones | Prompt en `config/base.yaml`; aviso de «producto sin ficha»; `README.md` §7 y `eval/analisis_resultados.md` | ⚠️ (falla con productos inexistentes sin parecido, p. ej. e12 en v1) |
| Latencias y tokens/s | `metricas/rag_latencia.md` | ✅ |

## Restricciones tecnológicas y arquitectura (15 %)

| Requisito | Evidencia | Estado |
|---|---|---|
| Solo open source, sin APIs de pago (tampoco para evaluar) | Ollama local; RAGAS con LLM local (`llama3.1:8b`). RAGAS instala `langchain-openai` como dependencia pero no se usa | ✅ |
| Documentar hardware y consumo | `metricas/hardware.md`, `extraccion_resumen.md`, `rag_latencia.md`, `evaluacion_consumo.md`; costo AWS < US$ 1 | ✅ |
| Justificar la arquitectura (desempeño, costo, complejidad) | `README.md` §1: el Learner Lab niega instancias mayores a *large*; mediciones EC2 contra PC (1.7 contra 8.3 tokens/s; 17 contra 2.4 s/página) | ✅ |
| Repositorio con código, dependencias fijadas y README (ejecución, arquitectura, modelos, decisiones) | `requirements.txt` (versiones fijas), `requirements-rag.txt` (solo RAG + evaluación), `README.md`, `infra/` (AWS por CLI), `scripts/` | ✅ |

## Evaluación con RAGAS (20 %)

| Requisito | Evidencia | Estado |
|---|---|---|
| 12 preguntas: 6 directas, 4 integradoras o comparativas, 2 sin respuesta; ≥ 4 secciones; productos identificados | `eval/preguntas.json` (9 secciones; una compara dos versiones del mismo producto); `python -m rag_fds.validar_preguntas` | ✅ |
| Referencias verificadas contra los PDF, con fragmento, documento, página y sección; fuera del índice y del prompt | Evidencia literal comprobada por código; **verificadas por el autor** (12 de 12, `eval/verificacion_preguntas_autor.json`); el código de indexado y generación no lee `eval/` | ✅ |
| Dos configuraciones que solo cambian top-k; el resto constante; preguntas de desarrollo distintas | `config/base.yaml`, `topk3.yaml`, `topk6.yaml` (comprobado por `config.verificar_solo_topk`); `eval/preguntas_desarrollo.json` | ✅ |
| Faithfulness, Context Precision y Context Recall en las 10 respondibles, ambas configuraciones | `eval/resultados_topk3.{csv,json}`, `eval/resultados_topk6.{csv,json}` | ✅ |
| Guardar por pregunta y configuración: `user_input`, `retrieved_contexts` (en orden), `response`, `reference`, fuentes, puntuaciones | Esos campos en los CSV/JSON anteriores (más errores y tiempos) | ✅ |
| Resultados por pregunta, promedios por métrica y número de casos válidos; fallos como tales | `eval/resumen.csv`; el fallo de e09 está como `NaN` con su mensaje de error | ✅ |
| Evaluador local probado primero con 2 casos; versiones y parámetros; el mismo en ambas | `eval/pilotos_evaluador.json` → `eval/piloto_evaluador.json`; `docs/evaluacion_ragas.md` (RAGAS 0.4.4, `llama3.1:8b`, temperatura 0, `num_ctx` 8 192, 1 trabajador) | ✅ |
| Revisión por separado de las 2 sin respuesta y de 3 respondibles (incluidas las de menor puntuación); exactitud y citas contra el PDF | `eval/revision_manual.md` y `eval/revision_manual/index.html` (plantilla y datos); `eval/revision_asistida_ia.md` (revisión contra el PDF hecha con IA) | ⏳ |
| Justificar la configuración elegida y explicar los errores | `eval/analisis_resultados.md` (errores por causa; se elige top-k 6; «comparación didáctica, no prueba general») | ✅ |

## Entregables y presentación (documentación y demostración, 10 %)

| Entregable | Archivo | Estado |
|---|---|---|
| 1. Repositorio con código, dependencias y README | <https://github.com/MrDavid0607/rag-fds> (público) | ✅ |
| 2. Markdown y recursos de todas las FDS con evidencia de verificación | `data/processed/`, `verificacion/` | ⏳ (ver arriba) |
| 3. Script de evaluación, preguntas y resultados en CSV/JSON | `src/rag_fds/evaluacion.py`, `scripts/correr_evaluacion.ps1`, `eval/` | ✅ |
| 4. Informe de máximo 2 páginas | `informe/informe.pdf` (fuente `informe/informe.md`) | ✅ |
| 5. Demostración funcional y explicación de decisiones | `app/demo.py`, `informe/guion_demo.md` (con preguntas probables del docente) | ✅ |

## Lo que NO se hizo y por qué
- **La verificación humana de la extracción y de los 5 casos analizados**: solo existe la revisión automática y asistida por IA, descrita arriba. Es lo único que impide marcar todo como ✅.
- **No se corrigieron** los problemas de extracción hallados (p. ej. códigos de peligro perdidos en la FDS 31, pág. 2; íconos leídos como ideogramas); están documentados como limitaciones.
- **Los PDF originales no están en el repositorio** (`data/raw/` en `.gitignore`); los Markdown y las imágenes extraídas sí.
