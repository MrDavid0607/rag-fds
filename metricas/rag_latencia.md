# Latencia del RAG (Fase 4)

Hardware: PC del autor (RTX 3050 de 4 GB, i5-11400H, 16 GB RAM). Ollama 0.40.16. Generador `qwen2.5:7b-instruct` (reparte la carga entre GPU y CPU).
Medido con las 6 preguntas de desarrollo (`python -m rag_fds.desarrollo`); los datos por pregunta están en `eval/desarrollo_topk{3,6}.json`.

| Configuración | Recuperación (mediana) | Generación (media) | Tokens/s | Tokens del prompt (medio) | Total por pregunta |
|---|---|---|---|---|---|
| top-k 3 | 6.97 s | 20.6 s | 9.3 | 1 281 | 27.5 s |
| top-k 6 | 7.46 s | 25.5 s | 8.2 | 1 930 | 33.0 s |

La recuperación de ~7 s se debe sobre todo a que Ollama debe volver a cargar `bge-m3` después del generador (no caben juntos en 4 GB de VRAM).
Con `bge-m3` ya cargado, la consulta al índice tarda entre 0.05 y 0.3 s.

Índice: 6 483 fragmentos embebidos en 272 s (23.8 fragmentos/s); `indice/chroma/` ocupa ≈ 67 MB; `indice/chunks.jsonl` ≈ 23 MB (ambos se regeneran y no van al repo).
