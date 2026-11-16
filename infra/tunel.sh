#!/usr/bin/env bash
# Túnel SSH: Ollama (11434) y la app de demo (8501) quedan en localhost del PC.
# Nunca se abren esos puertos en AWS. Dejar corriendo; Ctrl+C para cerrar.
set -euo pipefail
source "$(dirname "$0")/_comun.sh"
exigir_instancia
IP="$(ip_publica "$ID")"
echo "Túnel activo: http://localhost:11434 (Ollama) y http://localhost:8501 (demo). Ctrl+C para cerrar."
exec ssh "${OPCIONES_SSH[@]}" -N \
  -L 11434:127.0.0.1:11434 -L 8501:127.0.0.1:8501 "${USUARIO_EC2}@${IP}"
