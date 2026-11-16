# Mide velocidad de Ollama (tokens/s) en una instancia dada, con prompt largo (tipo RAG).
# Uso: powershell -File metricas\bench_ollama.ps1 -Modelo llama3.2:3b -Url http://localhost:11434 [-NumGpu 0]
param(
  [string]$Modelo = "llama3.2:3b",
  [string]$Url = "http://localhost:11434",
  [int]$NumGpu = -1   # -1 = automatico (usa GPU si hay); 0 = solo CPU
)
$ctx = ("La pintura base agua se debe almacenar en recipientes cerrados, en lugar fresco y ventilado, lejos de fuentes de ignicion. " * 40)
$prompt = "Contexto:`n$ctx`n`nPregunta: Como se debe almacenar la pintura? Responde en dos frases."
$opts = @{ temperature = 0; seed = 42; num_predict = 80; num_ctx = 4096 }
if ($NumGpu -ge 0) { $opts.num_gpu = $NumGpu }
$body = @{ model = $Modelo; prompt = $prompt; stream = $false; options = $opts } | ConvertTo-Json -Depth 4
# la primera llamada carga el modelo; la segunda es la medicion
$null = Invoke-RestMethod -Uri "$Url/api/generate" -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 900
$r = Invoke-RestMethod -Uri "$Url/api/generate" -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 900
[pscustomobject]@{
  modelo       = $Modelo
  num_gpu      = $NumGpu
  prompt_tok   = $r.prompt_eval_count
  prompt_tok_s = [math]::Round($r.prompt_eval_count / ($r.prompt_eval_duration / 1e9), 1)
  gen_tok      = $r.eval_count
  gen_tok_s    = [math]::Round($r.eval_count / ($r.eval_duration / 1e9), 1)
  total_s      = [math]::Round($r.total_duration / 1e9, 1)
} | Format-List
