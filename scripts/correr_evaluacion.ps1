# Corre la evaluación completa (Fase 6): genera respuestas y puntúa con RAGAS para topk3 y topk6, y calcula el resumen.
# Requiere Ollama local con qwen2.5:7b-instruct, bge-m3 y llama3.1:8b, y el índice construido.
# Uso (desde la raíz del repo):  powershell -File scripts\correr_evaluacion.ps1
$ErrorActionPreference = "Continue"
$env:PYTHONPATH = "src"
$env:PYTHONIOENCODING = "utf-8"
$py = ".\.venv\Scripts\python.exe"
$t0 = Get-Date

foreach ($k in "topk3", "topk6") { & $py -m rag_fds.evaluacion generar --config "config/$k.yaml" }
$t1 = Get-Date
foreach ($k in "topk3", "topk6") { & $py -m rag_fds.evaluacion puntuar --config "config/$k.yaml" }
$t2 = Get-Date
& $py -m rag_fds.evaluacion resumen

"TIEMPO_GENERACION_MIN: " + [math]::Round(($t1 - $t0).TotalMinutes, 1)
"TIEMPO_PUNTUACION_MIN: " + [math]::Round(($t2 - $t1).TotalMinutes, 1)
"TIEMPO_TOTAL_MIN: " + [math]::Round(((Get-Date) - $t0).TotalMinutes, 1)
"FIN"
