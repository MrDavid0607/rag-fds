#!/usr/bin/env bash
# Trae de la EC2 los resultados (Markdown extraído, verificación, evaluación, métricas, índice opcional).
set -euo pipefail
source "$(dirname "$0")/_comun.sh"
exigir_instancia
IP="$(ip_publica "$ID")"
cd "$RAIZ_REPO"
ssh "${OPCIONES_SSH[@]}" "${USUARIO_EC2}@${IP}" \
  "cd ~/${DIR_REMOTO} && tar -czf - \$(ls -d data/processed verificacion eval metricas 2>/dev/null)" \
  | tar -xzf - -C "$RAIZ_REPO"
echo "Resultados descargados al repo local."
