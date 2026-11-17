#!/usr/bin/env bash
# Se ejecuta EN LA EC2 (desde ~/rag-fds). Extrae fichas con Docling.
#   bash infra/remoto_extraer.sh <etiqueta> [numeros FDS...]
# Sin números procesa las 101. Las métricas quedan en metricas/extraccion_<etiqueta>.json.
set -euo pipefail
cd ~/rag-fds
. .venv/bin/activate
ETIQUETA="${1:-completa}"; shift || true
export PYTHONPATH=src
if [ "$#" -gt 0 ]; then
  python -m rag_fds.extraccion --entrada "data/raw/FDS EVALUADAS" --salida data/processed \
    --metricas "metricas/extraccion_${ETIQUETA}.json" --numeros "$@"
else
  python -m rag_fds.extraccion --entrada "data/raw/FDS EVALUADAS" --salida data/processed \
    --metricas "metricas/extraccion_${ETIQUETA}.json"
fi
