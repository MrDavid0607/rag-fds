# Evaluación con RAGAS (Fase 6)

Estado: **evaluación completa corrida** (2026-11-16/17) sobre las 10 preguntas respondibles, en las dos configuraciones. **Nota de trazabilidad:** la corrida se hizo cuando las 12 preguntas
estaban marcadas `"verificada": true` por una declaración del autor que luego se retiró (pasaron a `false` el 2026-11-17); ese mismo día el autor las verificó contra los PDF con `eval/revision_preguntas/index.html`
(12 de 12 «verificada», sin cambios; registro en `eval/verificacion_preguntas_autor.json`) y volvieron a `true`. Como ninguna referencia cambió, los resultados no se repitieron. Las puntuaciones de RAGAS orientan la
comparación y **requieren revisión manual** (Fase 7); no demuestran que una configuración sea mejor en general.

## Resultados (eval/resumen.csv; detalle por pregunta en eval/resultados_topk{3,6}.{csv,json})

| Configuración | Faithfulness (prom.) | Context Precision (prom.) | Context Recall (prom.) | Casos válidos F / CP / CR |
|---|---|---|---|---|
| top-k 3 | 0.892 | 1.000 | 0.910 | 10 / 10 / 10 |
| top-k 6 | 0.867 | 1.000 | 1.000 | 10 / 10 / **9** |

Por pregunta (F = Faithfulness, CP = Context Precision, CR = Context Recall):

| id | tipo | top-k 3 (F · CP · CR) | top-k 6 (F · CP · CR) |
|---|---|---|---|
| e01 | directa | 1.00 · 1.00 · 1.00 | 1.00 · 1.00 · 1.00 |
| e02 | directa | 1.00 · 1.00 · 1.00 | 1.00 · 1.00 · 1.00 |
| e03 | directa | 1.00 · 1.00 · 1.00 | 1.00 · 1.00 · 1.00 |
| e04 | directa | 0.50 · 1.00 · 1.00 | 0.50 · 1.00 · 1.00 |
| e05 | directa | 1.00 · 1.00 · 1.00 | 1.00 · 1.00 · 1.00 |
| e06 | directa | 1.00 · 1.00 · 1.00 | 1.00 · 1.00 · 1.00 |
| e07 | comparativa de versiones | 0.75 · 1.00 · 0.60 | 0.50 · 1.00 · 1.00 |
| e08 | integradora (secc. 2 y 5) | 0.67 · 1.00 · 1.00 | 1.00 · 1.00 · 1.00 |
| e09 | comparativa de productos | 1.00 · 1.00 · 1.00 | 0.67 · 1.00 · **NaN** |
| e10 | integradora (secc. 4 y 7) | 1.00 · 1.00 · 0.50 | 1.00 · 1.00 · 1.00 |

### Fallo del evaluador (registrado, no convertido en 0)
En **e09 con top-k 6**, Context Recall falló dos veces con `RagasOutputParserException: The output parser failed to parse the output including retries`
(la salida JSON de `llama3.1:8b` no se pudo interpretar; la llamada tardó ~20 min por los reintentos internos). Se reintentó una vez sin cambiar el
evaluador y volvió a fallar. Queda como `NaN` con su mensaje, por eso Context Recall de top-k 6 se promedia sobre **9 casos válidos**.

### Lectura prudente de los resultados
- **Context Precision = 1.00 en los 20 casos**: no discrimina. Con el filtro por producto casi todos los fragmentos recuperados son del documento correcto y el evaluador
  los juzga relevantes; es un "techo", no una prueba de recuperación perfecta.
- **Context Recall** es mayor con top-k 6 (1.00 contra 0.91), pero el promedio de top-k 6 excluye el caso fallido e09; la diferencia sale de e07 (0.60 → 1.00) y e10 (0.50 → 1.00).
- **Faithfulness** es algo menor con top-k 6 (0.87 contra 0.89) por e07 (0.75 → 0.50) y e09 (1.00 → 0.67), compensado por e08 (0.67 → 1.00). Con 10 preguntas y un
  evaluador de 8B, esas diferencias son del orden del ruido; deben revisarse a mano.
- e04 sale con Faithfulness 0.50 en ambas configuraciones aunque la respuesta parece correcta (7 - <10 % y CAS 13463-67-7): posible artefacto del evaluador, a revisar.
- Las **2 preguntas sin respuesta** no se puntúan con RAGAS (`eval/sin_respuesta_topk{3,6}.json`): e11 reconoce la falta de evidencia en ambas configuraciones. **e12 (Intergard
  475HS, producto inexistente): en la corrida v1 NO la reconocía en ninguna** (respondía con primeros auxilios de otro producto); en la v2, tras corregir el nombre de producto de 8 fichas AkzoNobel, **sí la reconoce en ambas** (resultado frágil; ver `eval/analisis_resultados.md`).

### Dos corridas (v1 y v2)
La corrida v1 mostró en la lista de fuentes de e12 un nombre de producto erróneo («X International.») en 8 fichas AkzoNobel. Se corrigió `metadatos.py`, se reconstruyeron fragmentos e índice y se repitió la evaluación completa (v2, 2026-11-17).
`python -m rag_fds.comparar_versiones` muestra que las 11 preguntas distintas de e12 recuperaron los mismos fragmentos y dieron las mismas respuestas, y que las **30 puntuaciones de RAGAS salieron idénticas** (incluido el fallo de Context Recall de e09 con top-k 6). Los resultados de v1 están en `eval/v1_antes_correccion_metadatos/`.
Las tablas de este documento valen para ambas versiones.

## Consumo y tiempos
Ver `metricas/evaluacion_consumo.md`.

## Preparación y prueba del evaluador (antes de la corrida)

## Configuración registrada (la misma en topk3 y topk6)

| Elemento | Valor |
|---|---|
| Métricas | Faithfulness · Context Precision **con referencia** (`LLMContextPrecisionWithReference`) · Context Recall (`LLMContextRecall`) |
| RAGAS | `ragas==0.4.4` (clases `ragas.metrics._faithfulness/_context_precision/_context_recall`) |
| Integración local | `langchain-ollama==1.1.0` → `ChatOllama` → `ragas.llms.base.LangchainLLMWrapper` (en 0.4.4 el envoltorio de LangChain está marcado como obsoleto, pero funciona; la API nueva exige un cliente tipo OpenAI, que no se usa) |
| Otras versiones | `langchain==1.5.0`, `langchain-core==1.8.1`, `ollama==0.6.3`, `datasets==5.2.0` |
| LLM evaluador | **`llama3.1:8b`** (Q4_K_M, digest `46e0c10c039e…`), **distinto** del generador (`qwen2.5:7b-instruct`) para reducir el sesgo de autoevaluación |
| Parámetros del evaluador | temperatura 0, semilla 42, `num_ctx` 8 192, `num_predict` 2 048, salida en JSON (`format="json"`) |
| Ejecución | 1 trabajador (`max_workers=1`), timeout 1 800 s por llamada, 3 reintentos |
| Embeddings | No se usan: las tres métricas son solo de LLM. (Los embeddings del RAG son `bge-m3`.) |
| Fallos | Se guardan como `NaN` + mensaje de error (`error_<métrica>`); nunca como 0. `resumen.csv` reporta además el número de casos válidos |
| Hardware | RTX 3050 de 4 GB + i5-11400H: el 8B corre repartido 64 % CPU / 36 % GPU |

No se usó ninguna API de pago. (`pip` instala `langchain-openai` como dependencia de RAGAS, pero no se importa ni se llama a ningún servicio de OpenAI.)

## Prueba con 2 casos (eval/pilotos_evaluador.json → eval/piloto_evaluador.json)

Los casos salen de preguntas de **desarrollo** (no de las 12 de evaluación) y llevan referencia con evidencia literal comprobada en el PDF.

| Caso | Faithfulness | Context Precision | Context Recall | Tiempo (3 métricas) |
|---|---|---|---|---|
| p1 · medios de extinción Topcoat 400 1793 | 1.00 | 1.00 | 1.00 | ≈ 180 s |
| p2 · teléfono de emergencia Sikafloor-2430 A | 1.00 (**0.67 si se dejan las citas**) | 0.95 | 1.00 | ≈ 100 s |

Sin errores del evaluador (JSON válido en todas las llamadas).

### Hallazgo: las citas `[n]` ensucian la Faithfulness
En el primer intento, p2 salió con Faithfulness 0.67 aunque la respuesta era correcta. Con `python -m rag_fds.diagnostico_evaluador p2 --con-citas`
se ve la causa: el evaluador descompone la respuesta en afirmaciones y trata las marcas de cita como una más
("*The phone number 01 8000 916012 is [1][4].*"), que marca como no respaldada. Es un artefacto de medición, no un error de contenido.

**Decisión (igual para topk3 y topk6, fijada antes de evaluar):** para *puntuar*, se quitan las marcas `[n]` de la respuesta
(`quitar_citas`); la respuesta **original con citas** es la que se guarda y la que se revisa a mano. La corrección de las citas (que
apunten a la página y sección correctas) no la mide RAGAS: la comprueba el autor en la Fase 7.

### Otras observaciones del evaluador
- RAGAS genera las afirmaciones **en inglés** aunque la respuesta esté en español; el evaluador las contrasta bien con contextos en español.
- Los dos casos piloto son fáciles: sirven para comprobar que el mecanismo funciona (JSON válido, puntuaciones coherentes con el diagnóstico paso a paso),
  no para demostrar que el evaluador discrimine bien casos malos. Las puntuaciones de RAGAS siguen requiriendo revisión manual.
- Coste: ~1.5-3.5 min por pregunta con top-k 6 (Context Precision hace una llamada por fragmento recuperado). Estimado para las 10 respondibles en ambas
  configuraciones: ≈ 1 h de evaluación más ≈ 10 min de generación.

## Cómo se correrá cuando las preguntas estén verificadas

```bash
python -m rag_fds.evaluacion generar --config config/topk3.yaml
python -m rag_fds.evaluacion generar --config config/topk6.yaml
python -m rag_fds.evaluacion puntuar --config config/topk3.yaml
python -m rag_fds.evaluacion puntuar --config config/topk6.yaml
python -m rag_fds.evaluacion resumen
```

Genera `eval/respuestas_topk{3,6}.json`, `eval/resultados_topk{3,6}.{csv,json}` (con `user_input`, `retrieved_contexts` en orden, `response`, `reference`,
`fuentes`, puntuaciones y errores), `eval/sin_respuesta_topk{3,6}.json` (las 2 sin respuesta, que no se puntúan con RAGAS) y `eval/resumen.csv`
(promedio por métrica y configuración y número de casos válidos).
