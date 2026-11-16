#!/usr/bin/env bash
# Túnel SSH: Ollama de la EC2 (11435) y la app de demo (8501) quedan en localhost del PC.
# Nunca se abren esos puertos en AWS. Dejar corriendo; Ctrl+C para cerrar.
set -euo pipefail
source "$(dirname "$0")/_comun.sh"
exigir_instancia
IP="$(ip_publica "$ID")"
# El Ollama de la EC2 se ve en el puerto 11435 del PC, porque el 11434 lo usa el Ollama local (GPU).
echo "Túnel activo: http://localhost:11435 (Ollama de la EC2) y http://localhost:8501 (demo). Ctrl+C para cerrar."
exec ssh "${OPCIONES_SSH[@]}" -N \
  -L 11435:127.0.0.1:11434 -L 8501:127.0.0.1:8501 "${USUARIO_EC2}@${IP}"
