# Consumo de la evaluación con RAGAS (Fase 6)

Corrida v1 del 2026-11-16 (noche) al 2026-11-17, en el PC del autor (RTX 3050 de 4 GB, i5-11400H, 16 GB RAM, Windows 11). Script: `scripts/correr_evaluacion.ps1`.
No se usó la EC2 ni ningún servicio de pago: costo en AWS de esta fase = 0.

| Etapa | Tiempo |
|---|---|
| Generar respuestas (12 preguntas × 2 configuraciones, `qwen2.5:7b-instruct`) | 12.2 min |
| Puntuar con RAGAS, top-k 3 (10 preguntas, `llama3.1:8b`) | 19.4 min (1 162 s) |
| Puntuar con RAGAS, top-k 6 (10 preguntas) | 36.2 min (2 174 s) |
| Reintento de Context Recall en e09 top-k 6 (volvió a fallar) | 22.1 min (1 325 s, repite las 3 métricas de esa pregunta) |
| **Total** | **≈ 90 min** |

Generación (media por pregunta): top-k 3 → 20.6 s y ~1 208 tokens de prompt; top-k 6 → 24.3 s y ~1 995 tokens de prompt.
Evaluación: ~2 min por pregunta con top-k 3 y ~3.6 min con top-k 6 (Context Precision hace una llamada por fragmento); el caso que falló consumió ~20 min en reintentos internos.

Modelos y versiones: ver `docs/evaluacion_ragas.md` (evaluador `llama3.1:8b`, RAGAS 0.4.4, `langchain-ollama` 1.1.0, temperatura 0, `num_ctx` 8 192).
Memoria: el evaluador de 8B corre repartido entre CPU (64 %) y GPU (36 %); el generador y `bge-m3` se reemplazan en la VRAM entre etapas.

## Repetición completa tras corregir los metadatos (v2, 2026-11-17)

Tras corregir el nombre de producto de 8 fichas AkzoNobel (ver `verificacion/errores_extraccion.md`, hallazgo 16) se reconstruyó el índice (246 s) y se repitió la evaluación (`scripts/correr_evaluacion.ps1`):

| Etapa | Tiempo |
|---|---|
| Generar respuestas (12 preguntas × 2 configuraciones) | 12.3 min |
| Puntuar con RAGAS, top-k 3 | 17.5 min (1 048 s) |
| Puntuar con RAGAS, top-k 6 | 34.6 min (2 078 s) |
| **Total** | **64.7 min** |

Generación media por pregunta: top-k 3 → 21.1 s; top-k 6 → 25.2 s. Costo en AWS: 0 (la EC2 sigue detenida).