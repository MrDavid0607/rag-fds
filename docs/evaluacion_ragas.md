# Evaluación con RAGAS (Fase 6) — preparación y prueba del evaluador

Estado: **evaluador probado con 2 casos piloto; la evaluación completa NO se ha corrido** porque las 12 preguntas aún no están
verificadas por el autor (`"verificada": true` en `eval/preguntas.json`). Sin esa marca, `evaluacion.py generar` se niega a ejecutar.

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
